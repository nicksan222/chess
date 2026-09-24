//! Control-panel buttons: debounce GPIO levels and publish typed events.

use std::{error::Error as StdError, fmt};

use tokio::{runtime::Handle, task::JoinHandle, time::Instant};

use crate::events::{Bus, ReceiveError, Subscription};

use super::{
    HardwareEventBus,
    debounce::{Debouncer, POLL_INTERVAL},
    pins::{GPIO, Level, ReadLevel},
};

/// The label printed beside a physical control-panel button.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Button {
    Up,
    Down,
    Left,
    Right,
    Ok,
    Reset,
    Pass,
    F1,
    F2,
    F3,
    F4,
    F5,
}

/// A debounced electrical transition produced by a physical button adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ButtonEvent {
    Pressed(Button),
    Released(Button),
}

/// A debounced physical transition from one panel button.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ButtonAction {
    Pressed,
    Released,
}

/// A control-panel button connected directly to a GPIO input.
pub struct ButtonPin<const BCM: u8> {
    gpio: GPIO,
    button: Button,
}

impl<const BCM: u8> ButtonPin<BCM> {
    pub(super) const fn new(button: Button) -> Self {
        Self {
            gpio: GPIO::new(BCM),
            button,
        }
    }

    pub const fn gpio(&self) -> GPIO {
        self.gpio
    }

    pub const fn bcm_number(&self) -> u8 {
        BCM
    }

    /// Returns the physical panel label assigned to this pin.
    pub const fn button(&self) -> Button {
        self.button
    }

    pub fn read_level<R: ReadLevel>(&self, reader: &mut R) -> Result<Level, R::Error> {
        reader.read_level(self.gpio)
    }

    /// Starts polling and debouncing this button.
    pub fn start_subscription<R>(
        &self,
        reader: R,
        events: &HardwareEventBus,
    ) -> Result<ButtonSubscription, StartSubscriptionError>
    where
        R: ReadLevel + Send + 'static,
    {
        let runtime = Handle::try_current().map_err(|_| StartSubscriptionError)?;
        let button_events = Bus::new();
        let event_subscription = button_events.subscribe();
        let worker = runtime.spawn(poll(
            self.gpio,
            self.button,
            reader,
            events.clone(),
            button_events,
        ));

        Ok(ButtonSubscription {
            button: self.button,
            events: event_subscription,
            worker,
        })
    }
}

/// A running button poller and its domain-level event subscription.
#[derive(Debug)]
pub struct ButtonSubscription {
    button: Button,
    events: Subscription<ButtonEvent>,
    worker: JoinHandle<()>,
}

impl ButtonSubscription {
    /// Waits for the next debounced transition from this button.
    pub async fn on_message(&mut self) -> Result<ButtonAction, ReceiveError> {
        loop {
            match self.events.recv().await? {
                ButtonEvent::Pressed(button) if button == self.button => {
                    return Ok(ButtonAction::Pressed);
                }
                ButtonEvent::Released(button) if button == self.button => {
                    return Ok(ButtonAction::Released);
                }
                ButtonEvent::Pressed(_) | ButtonEvent::Released(_) => {}
            }
        }
    }
}

impl Drop for ButtonSubscription {
    fn drop(&mut self) {
        self.worker.abort();
    }
}

/// Starting a button subscription requires an active Tokio runtime.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct StartSubscriptionError;

impl fmt::Display for StartSubscriptionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("button subscriptions require an active Tokio runtime")
    }
}

impl StdError for StartSubscriptionError {}

async fn poll<R>(
    gpio: GPIO,
    button: Button,
    mut reader: R,
    hardware_events: HardwareEventBus,
    button_events: Bus<ButtonEvent>,
) where
    R: ReadLevel,
{
    let mut interval = tokio::time::interval(POLL_INTERVAL);
    interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
    let mut debouncer: Option<Debouncer> = None;
    let mut read_failed = false;

    loop {
        interval.tick().await;

        let Ok(level) = reader.read_level(gpio) else {
            if !read_failed {
                logger::warn!("button GPIO {} read failed", gpio.bcm_number());
            }
            read_failed = true;
            if let Some(debouncer) = &mut debouncer {
                debouncer.interrupt();
            }
            continue;
        };
        read_failed = false;

        let debouncer = debouncer.get_or_insert_with(|| Debouncer::new(level));
        let Some(action) = debouncer.observe(level, Instant::now()) else {
            continue;
        };

        let event = match action {
            ButtonAction::Pressed => ButtonEvent::Pressed(button),
            ButtonAction::Released => ButtonEvent::Released(button),
        };
        if button_events.emit(event).is_err() {
            return;
        }
        // The local subscription above owns delivery to `on_message`; the
        // shared bus independently bridges the observation into the runtime.
        let _ = hardware_events.emit(event.into());
    }
}

#[cfg(test)]
mod tests {
    use std::{collections::VecDeque, time::Duration};

    use super::*;
    use crate::hardware::pins::BoardPins;

    #[test]
    fn starting_a_button_subscription_without_a_runtime_returns_an_error() {
        let events = HardwareEventBus::new();
        let reader = SequenceReader {
            levels: VecDeque::from([Level::High]),
        };
        let error = BoardPins::get()
            .gpio
            .down_button
            .start_subscription(reader, &events)
            .unwrap_err();
        assert_eq!(
            error.to_string(),
            "button subscriptions require an active Tokio runtime"
        );
    }

    struct SequenceReader {
        levels: VecDeque<Level>,
    }

    impl ReadLevel for SequenceReader {
        type Error = ();

        fn read_level(&mut self, _: GPIO) -> Result<Level, Self::Error> {
            self.levels.pop_front().ok_or(())
        }
    }

    #[tokio::test(start_paused = true)]
    async fn button_pins_poll_debounce_and_deliver_physical_transitions() {
        let events = HardwareEventBus::new();
        let reader = SequenceReader {
            levels: VecDeque::from([
                Level::High,
                Level::Low,
                Level::Low,
                Level::Low,
                Level::Low,
                Level::Low,
            ]),
        };
        let mut next = BoardPins::get()
            .gpio
            .down_button
            .start_subscription(reader, &events)
            .unwrap();
        let action = tokio::time::timeout(Duration::from_millis(100), next.on_message())
            .await
            .expect("button poller should produce an action")
            .unwrap();
        assert_eq!(action, ButtonAction::Pressed);
    }
}
