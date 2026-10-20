//! Owns the twelve physical button pollers for the lifetime of the application.

use std::{fmt::Display, io};

use logger::{error, info};

use super::{
    HardwareEventBus,
    pins::{BoardPins, ButtonPin, ButtonSubscription, ReadLevel},
};

/// Dropping the panel stops all pollers and releases their GPIO requests.
/// Startup errors roll back already-started pollers; no partial panel is returned.
pub struct ButtonPanel {
    _subscriptions: Vec<ButtonSubscription>,
}

impl ButtonPanel {
    /// Requests the board's inputs with internal pull-ups on the selected chip.
    /// Logs the startup outcome and returns an error with chip, button and GPIO
    /// context if acquisition fails. No partial panel is returned.
    #[cfg(target_os = "linux")]
    pub fn open(chip: impl AsRef<std::path::Path>, events: &HardwareEventBus) -> io::Result<Self> {
        let chip = chip.as_ref();
        info!(
            "opening control-panel buttons on {} with internal pull-ups",
            chip.display()
        );
        match Self::start(|| super::linux_gpio::LinuxGpioReader::new(chip), events) {
            Ok(panel) => {
                info!(
                    "control-panel buttons ready on {}: {} inputs initialized, pollers started",
                    chip.display(),
                    panel._subscriptions.len()
                );
                Ok(panel)
            }
            Err(cause) => {
                let error = io::Error::new(
                    cause.kind(),
                    format!(
                        "opening control-panel buttons on {}: {cause}",
                        chip.display()
                    ),
                );
                error!("{error}; firmware startup cannot continue");
                Err(error)
            }
        }
    }

    /// Starts the same panel with injected readers, one owned reader per button.
    /// Every line is read before its poller starts, so acquisition errors fail
    /// startup and an initially held button establishes a baseline without a press.
    pub fn start<R>(mut reader: impl FnMut() -> R, events: &HardwareEventBus) -> io::Result<Self>
    where
        R: ReadLevel + Send + 'static,
        R::Error: Display,
    {
        tokio::runtime::Handle::try_current()
            .map_err(|_| io::Error::other("button panel requires an active Tokio runtime"))?;
        let pins = BoardPins::get().gpio;
        let mut subscriptions = Vec::with_capacity(12);
        macro_rules! attach {
            ($($pin:ident),+ $(,)?) => {$(
                subscriptions.push(start(&pins.$pin, reader(), events)?);
            )+};
        }
        attach!(
            up_button,
            down_button,
            left_button,
            right_button,
            ok_button,
            reset_button,
            pass_button,
            function_one_button,
            function_two_button,
            function_three_button,
            function_four_button,
            function_five_button,
        );
        Ok(Self {
            _subscriptions: subscriptions,
        })
    }
}

fn start<const BCM: u8, R>(
    pin: &ButtonPin<BCM>,
    mut reader: R,
    events: &HardwareEventBus,
) -> io::Result<ButtonSubscription>
where
    R: ReadLevel + Send + 'static,
    R::Error: Display,
{
    let initial = pin.read_level(&mut reader).map_err(|error| {
        io::Error::other(format!(
            "initializing {:?} button on GPIO {BCM}: {error}",
            pin.button()
        ))
    })?;
    pin.start_with_level(reader, events, Some(initial))
        .map_err(io::Error::other)
}

#[cfg(test)]
mod tests {
    use std::sync::{Arc, Mutex};
    use std::time::Duration;

    use super::*;
    use crate::{
        hardware::pins::{Button, ButtonEvent, GPIO, Level},
        runtime::Firmware,
    };

    struct State {
        levels: [Level; 28],
        fail: Option<u8>,
        live: usize,
        reads: usize,
    }

    struct Reader(Arc<Mutex<State>>);

    impl Reader {
        fn new(state: &Arc<Mutex<State>>) -> Self {
            state.lock().unwrap().live += 1;
            Self(Arc::clone(state))
        }
    }

    impl Drop for Reader {
        fn drop(&mut self) {
            self.0.lock().unwrap().live -= 1;
        }
    }

    impl ReadLevel for Reader {
        type Error = &'static str;

        fn read_level(&mut self, gpio: GPIO) -> Result<Level, Self::Error> {
            let mut state = self.0.lock().unwrap();
            state.reads += 1;
            if state.fail == Some(gpio.bcm_number()) {
                return Err("line busy");
            }
            Ok(state.levels[usize::from(gpio.bcm_number())])
        }
    }

    fn state() -> Arc<Mutex<State>> {
        Arc::new(Mutex::new(State {
            levels: [Level::High; 28],
            fail: None,
            live: 0,
            reads: 0,
        }))
    }

    #[tokio::test(start_paused = true)]
    async fn panel_drives_runtime_and_releases_all_readers_on_drop() {
        let state = state();
        // An already-held Up must establish a baseline without moving the menu.
        state.lock().unwrap().levels[5] = Level::Low;
        let mut firmware = Firmware::start().unwrap();
        let panel = ButtonPanel::start(|| Reader::new(&state), &firmware.events()).unwrap();
        assert_eq!(state.lock().unwrap().live, 12);
        tokio::time::sleep(Duration::from_millis(50)).await;
        assert_eq!(firmware.snapshot().processed_events, 0);

        state.lock().unwrap().levels[6] = Level::Low;
        let pressed = tokio::time::timeout(Duration::from_millis(100), firmware.after(0))
            .await
            .unwrap()
            .unwrap();
        assert_eq!(pressed.selected_index, 1);
        assert_eq!(
            pressed.last_event,
            Some(ButtonEvent::Pressed(Button::Down).into())
        );

        state.lock().unwrap().levels[6] = Level::High;
        let released = tokio::time::timeout(Duration::from_millis(100), firmware.after(1))
            .await
            .unwrap()
            .unwrap();
        assert_eq!(
            released.last_event,
            Some(ButtonEvent::Released(Button::Down).into())
        );
        drop(panel);
        tokio::task::yield_now().await;
        assert_eq!(state.lock().unwrap().live, 0);
        let reads = state.lock().unwrap().reads;
        tokio::time::sleep(Duration::from_millis(50)).await;
        assert_eq!(state.lock().unwrap().reads, reads);
        firmware.shutdown().await.unwrap();
    }

    #[tokio::test]
    async fn failed_acquisition_reports_the_line_and_rolls_back_the_panel() {
        let state = state();
        state.lock().unwrap().fail = Some(16);
        let error = ButtonPanel::start(|| Reader::new(&state), &HardwareEventBus::new())
            .err()
            .expect("busy OK line must fail startup");
        assert_eq!(
            error.to_string(),
            "initializing Ok button on GPIO 16: line busy"
        );
        tokio::task::yield_now().await;
        assert_eq!(state.lock().unwrap().live, 0);
    }

    #[test]
    fn no_runtime_fails_before_acquiring_gpio() {
        let state = state();
        let error = ButtonPanel::start(|| Reader::new(&state), &HardwareEventBus::new())
            .err()
            .expect("a runtime is required");
        assert!(error.to_string().contains("active Tokio runtime"));
        assert_eq!(state.lock().unwrap().reads, 0);
        assert_eq!(state.lock().unwrap().live, 0);
    }

    #[cfg(target_os = "linux")]
    #[tokio::test]
    async fn missing_chip_fails_panel_startup() {
        let error = ButtonPanel::open("/dev/gpiochip-does-not-exist", &HardwareEventBus::new())
            .err()
            .expect("a missing chip must fail startup");
        assert!(error.to_string().contains("Up button on GPIO 5"));
        assert!(
            error
                .to_string()
                .contains("opening control-panel buttons on /dev/gpiochip-does-not-exist")
        );
    }
}
