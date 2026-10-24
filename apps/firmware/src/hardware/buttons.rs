//! Control-panel buttons: debounce GPIO levels and publish typed events.

use std::{error::Error as StdError, fmt, ops::Deref, time::Duration};

use tokio::{runtime::Handle, task::JoinHandle, time::Instant};

use crate::{
    events::{Bus, ReceiveError, Subscription},
    tuning::ButtonTuning,
};

use super::{
    HardwareEventBus,
    debounce::Debouncer,
    pins::{GPIO, Input, Level, Pin, ReadLevel},
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

impl Button {
    /// The menu input this button drives, if it navigates the menu.
    pub fn menu_input(self) -> Option<::menu::Input> {
        use ::menu::Input;
        match self {
            Self::Up => Some(Input::Up),
            Self::Down => Some(Input::Down),
            Self::Left => Some(Input::Left),
            Self::Right => Some(Input::Right),
            Self::Ok => Some(Input::Ok),
            Self::Reset | Self::Pass | Self::F1 | Self::F2 | Self::F3 | Self::F4 | Self::F5 => None,
        }
    }
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
///
/// Dereferences to its [`Pin`] for the GPIO identity and level reads.
pub struct ButtonPin<const BCM: u8> {
    pin: Pin<BCM, Input>,
    button: Button,
}

impl<const BCM: u8> Deref for ButtonPin<BCM> {
    type Target = Pin<BCM, Input>;

    fn deref(&self) -> &Self::Target {
        &self.pin
    }
}

impl<const BCM: u8> ButtonPin<BCM> {
    pub(super) const fn new(button: Button) -> Self {
        Self {
            pin: Pin::new(),
            button,
        }
    }

    /// Returns the physical panel label assigned to this pin.
    pub const fn button(&self) -> Button {
        self.button
    }

    /// Starts polling and debouncing this button with the default
    /// [`ButtonTuning`].
    pub fn start_subscription<R>(
        &self,
        reader: R,
        events: &HardwareEventBus,
    ) -> Result<ButtonSubscription, StartSubscriptionError>
    where
        R: ReadLevel + Send + 'static,
    {
        self.start_with_level(reader, events, None, ButtonTuning::DEFAULT)
    }

    pub(super) fn start_with_level<R>(
        &self,
        reader: R,
        events: &HardwareEventBus,
        initial: Option<Level>,
        tuning: ButtonTuning,
    ) -> Result<ButtonSubscription, StartSubscriptionError>
    where
        R: ReadLevel + Send + 'static,
    {
        let runtime = Handle::try_current().map_err(|_| StartSubscriptionError)?;
        let button_events = Bus::new();
        let event_subscription = button_events.subscribe();
        let worker = runtime.spawn(poll(
            self.gpio(),
            self.button,
            reader,
            events.clone(),
            button_events,
            initial,
            tuning,
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

/// One button's sampling state: reads its GPIO, debounces, and reports edges.
/// Kept free of timers and buses so it can be stepped directly in tests.
struct ButtonPoller {
    gpio: GPIO,
    button: Button,
    debounce: Duration,
    debouncer: Option<Debouncer>,
    read_failed: bool,
}

impl ButtonPoller {
    fn new(gpio: GPIO, button: Button, initial: Option<Level>, debounce: Duration) -> Self {
        Self {
            gpio,
            button,
            debounce,
            debouncer: initial.map(|level| Debouncer::new(level, debounce)),
            read_failed: false,
        }
    }

    /// Samples the line once at `now`. A failed read is logged once per run of
    /// failures and restarts any debounce in progress; the first successful
    /// read becomes the baseline when none was supplied.
    fn step<R: ReadLevel>(&mut self, reader: &mut R, now: Instant) -> Option<ButtonEvent> {
        let Ok(level) = reader.read_level(self.gpio) else {
            if !self.read_failed {
                logger::warn!("button GPIO {} read failed", self.gpio.bcm_number());
            }
            self.read_failed = true;
            if let Some(debouncer) = &mut self.debouncer {
                debouncer.interrupt();
            }
            return None;
        };
        self.read_failed = false;

        let debounce = self.debounce;
        let debouncer = self
            .debouncer
            .get_or_insert_with(|| Debouncer::new(level, debounce));
        Some(match debouncer.observe(level, now)? {
            ButtonAction::Pressed => ButtonEvent::Pressed(self.button),
            ButtonAction::Released => ButtonEvent::Released(self.button),
        })
    }
}

async fn poll<R>(
    gpio: GPIO,
    button: Button,
    mut reader: R,
    hardware_events: HardwareEventBus,
    button_events: Bus<ButtonEvent>,
    initial: Option<Level>,
    tuning: ButtonTuning,
) where
    R: ReadLevel,
{
    let mut interval = tokio::time::interval(tuning.poll_interval);
    interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
    let mut poller = ButtonPoller::new(gpio, button, initial, tuning.debounce);

    loop {
        interval.tick().await;
        let Some(event) = poller.step(&mut reader, Instant::now()) else {
            continue;
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
    use std::{
        collections::VecDeque,
        sync::{
            Arc,
            atomic::{AtomicUsize, Ordering},
        },
    };

    use super::*;
    use crate::hardware::pins::BoardPins;

    #[test]
    fn the_poller_steps_through_debounce_failures_and_baseline() {
        let start = Instant::now();
        let ms = Duration::from_millis;
        let gpio = GPIO::new(5);
        let mut reader = SequenceReader {
            levels: VecDeque::from([Level::High, Level::Low, Level::Low]),
        };
        let mut poller = ButtonPoller::new(gpio, Button::Up, None, ButtonTuning::DEFAULT.debounce);

        // The first valid read is the baseline, not a press.
        assert_eq!(poller.step(&mut reader, start), None);
        assert_eq!(poller.step(&mut reader, start + ms(5)), None);
        assert_eq!(
            poller.step(&mut reader, start + ms(30)),
            Some(ButtonEvent::Pressed(Button::Up))
        );
        // A failed read (the script is exhausted) reports nothing.
        assert_eq!(poller.step(&mut reader, start + ms(35)), None);
    }

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

    /// Replays scripted samples (`None` is a failed read), then repeats `tail`.
    struct ScriptedReader {
        samples: VecDeque<Option<Level>>,
        tail: Option<Level>,
        reads: Arc<AtomicUsize>,
    }

    impl ScriptedReader {
        fn new(samples: &[Option<Level>], tail: Option<Level>) -> Self {
            Self {
                samples: samples.iter().copied().collect(),
                tail,
                reads: Arc::default(),
            }
        }
    }

    impl ReadLevel for ScriptedReader {
        type Error = ();

        fn read_level(&mut self, _: GPIO) -> Result<Level, Self::Error> {
            self.reads.fetch_add(1, Ordering::SeqCst);
            self.samples.pop_front().unwrap_or(self.tail).ok_or(())
        }
    }

    const STABLE: usize = 5; // Five 5-ms samples complete the 20-ms debounce.

    #[tokio::test(start_paused = true)]
    async fn two_held_buttons_each_publish_their_own_press_on_the_shared_bus() {
        let events = HardwareEventBus::new();
        let mut observed = events.subscribe();
        let pins = BoardPins::get().gpio;
        let mut samples = vec![Some(Level::High)];
        samples.extend([Some(Level::Low); STABLE]);
        let down = pins
            .down_button
            .start_subscription(ScriptedReader::new(&samples, Some(Level::Low)), &events)
            .unwrap();
        let up = pins
            .up_button
            .start_subscription(ScriptedReader::new(&samples, Some(Level::Low)), &events)
            .unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;

        let mut seen = Vec::new();
        while let Some(event) = observed.try_recv().unwrap() {
            seen.push(event);
        }
        assert_eq!(seen.len(), 2, "{seen:?}");
        for button in [Button::Down, Button::Up] {
            assert!(
                seen.contains(&ButtonEvent::Pressed(button).into()),
                "{button:?} missing from {seen:?}"
            );
        }
        drop((down, up));
    }

    /// Every pin owns its subscription, so one pin's presses never reach another pin's
    /// `on_message`. (`on_message` also filters by button, but that arm is not reachable
    /// through `start_subscription`; this test checks the isolation, not that filter.)
    #[tokio::test(start_paused = true)]
    async fn each_pin_subscription_is_isolated_from_the_other_pins() {
        let events = HardwareEventBus::new();
        let pins = BoardPins::get().gpio;
        let mut samples = vec![Some(Level::High)];
        samples.extend([Some(Level::Low); STABLE]);
        let mut up = pins
            .up_button
            .start_subscription(
                ScriptedReader::new(&[Some(Level::High)], Some(Level::High)),
                &events,
            )
            .unwrap();
        let _down = pins
            .down_button
            .start_subscription(ScriptedReader::new(&samples, Some(Level::Low)), &events)
            .unwrap();

        let waited = tokio::time::timeout(Duration::from_millis(200), up.on_message()).await;
        assert!(waited.is_err(), "Up must not report Down's press");
    }

    #[tokio::test(start_paused = true)]
    async fn dropping_the_subscription_stops_polling_the_reader() {
        let events = HardwareEventBus::new();
        let reader = ScriptedReader::new(&[], Some(Level::High));
        let reads = Arc::clone(&reader.reads);
        let subscription = BoardPins::get()
            .gpio
            .ok_button
            .start_subscription(reader, &events)
            .unwrap();

        tokio::time::sleep(Duration::from_millis(50)).await;
        assert!(reads.load(Ordering::SeqCst) >= 5);
        drop(subscription);
        tokio::time::sleep(Duration::from_millis(5)).await; // Let the abort land.
        let stopped = reads.load(Ordering::SeqCst);
        tokio::time::sleep(Duration::from_millis(100)).await;
        assert_eq!(reads.load(Ordering::SeqCst), stopped);
    }

    #[tokio::test(start_paused = true)]
    async fn a_failing_first_read_is_skipped_and_the_next_level_is_the_baseline() {
        let events = HardwareEventBus::new();
        let mut observed = events.subscribe();
        // The first valid sample (Low, a held button) must not invent a press.
        let reader = ScriptedReader::new(&[None, None, Some(Level::Low)], Some(Level::Low));
        let _subscription = BoardPins::get()
            .gpio
            .reset_button
            .start_subscription(reader, &events)
            .unwrap();

        tokio::time::sleep(Duration::from_millis(100)).await;

        assert_eq!(observed.try_recv(), Ok(None));
    }

    #[tokio::test(start_paused = true)]
    async fn a_reader_that_never_recovers_produces_no_events_and_no_panic() {
        let events = HardwareEventBus::new();
        let mut observed = events.subscribe();
        let reader = ScriptedReader::new(&[Some(Level::High)], None);
        let reads = Arc::clone(&reader.reads);
        let mut subscription = BoardPins::get()
            .gpio
            .pass_button
            .start_subscription(reader, &events)
            .unwrap();

        let waited =
            tokio::time::timeout(Duration::from_millis(500), subscription.on_message()).await;

        assert!(waited.is_err(), "no transition may be reported");
        assert_eq!(observed.try_recv(), Ok(None));
        assert!(reads.load(Ordering::SeqCst) > 50, "polling must continue");
    }

    #[tokio::test(start_paused = true)]
    async fn a_tuned_poll_interval_and_debounce_set_when_a_press_lands() {
        let events = HardwareEventBus::new();
        let mut observed = events.subscribe();
        let tuning = ButtonTuning {
            poll_interval: Duration::from_millis(10),
            debounce: Duration::from_millis(60),
        };
        let reader = ScriptedReader::new(&[Some(Level::High)], Some(Level::Low));
        let reads = Arc::clone(&reader.reads);
        let start = Instant::now();
        let mut subscription = BoardPins::get()
            .gpio
            .left_button
            .start_with_level(reader, &events, None, tuning)
            .unwrap();

        // Low is first seen at 10 ms; the default 20 ms debounce would report
        // it by 30 ms, the tuned 60 ms one only at 70 ms.
        tokio::time::sleep(Duration::from_millis(65)).await;
        assert_eq!(observed.try_recv(), Ok(None));
        assert_eq!(reads.load(Ordering::SeqCst), 7, "sampled every 10 ms");
        assert_eq!(subscription.on_message().await, Ok(ButtonAction::Pressed));
        assert_eq!(start.elapsed(), Duration::from_millis(70));
    }

    #[tokio::test(start_paused = true)]
    async fn a_press_interrupted_by_a_failed_read_restarts_its_debounce() {
        let events = HardwareEventBus::new();
        let mut subscription = BoardPins::get()
            .gpio
            .function_one_button
            .start_subscription(
                ScriptedReader::new(
                    &[
                        Some(Level::High),
                        Some(Level::Low),
                        Some(Level::Low),
                        Some(Level::Low),
                        Some(Level::Low), // Four of five stable samples...
                        None,             // ...then a failure forgets them.
                    ],
                    Some(Level::Low),
                ),
                &events,
            )
            .unwrap();
        let mut observed = events.subscribe();

        // Low was first seen at 5 ms. Without the restart the press would fire at 30 ms
        // (when the samples resume); with it, at 50 ms. Look strictly between.
        tokio::time::sleep(Duration::from_millis(42)).await;
        assert_eq!(observed.try_recv(), Ok(None));
        assert_eq!(subscription.on_message().await, Ok(ButtonAction::Pressed));
    }
}
