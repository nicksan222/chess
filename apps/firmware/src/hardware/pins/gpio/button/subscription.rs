use std::{error::Error as StdError, fmt};

use tokio::{runtime::Handle, task::JoinHandle, time::Instant};

use crate::events::{Bus, ReceiveError, Subscription};

use super::{Button, ButtonAction, ButtonEvent, debounce::Debouncer, debounce::POLL_INTERVAL};
use crate::hardware::{
    HardwareEventBus,
    pins::{GPIO, ReadLevel},
};

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

pub(super) fn start<R>(
    gpio: GPIO,
    button: Button,
    reader: R,
    events: &HardwareEventBus,
) -> Result<ButtonSubscription, StartSubscriptionError>
where
    R: ReadLevel + Send + 'static,
{
    let runtime = Handle::try_current().map_err(|_| StartSubscriptionError)?;
    let button_events = Bus::new();
    let event_subscription = button_events.subscribe();
    let worker = runtime.spawn(poll(gpio, button, reader, events.clone(), button_events));

    Ok(ButtonSubscription {
        button,
        events: event_subscription,
        worker,
    })
}

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
