use std::{collections::VecDeque, time::Duration};

use firmware::{
    hardware::{
        HardwareEvent,
        pins::{BoardPins, Button, ButtonEvent, ButtonPin, GPIO, Level, ReadLevel},
    },
    runtime::Firmware,
};

/// Feeds electrical levels to the button adapter; `None` simulates a read failure.
/// Production GPIO device access is not wired up yet.
struct SequenceReader {
    samples: VecDeque<Option<Level>>,
    last: Level,
}

impl ReadLevel for SequenceReader {
    type Error = ();

    fn read_level(&mut self, _: GPIO) -> Result<Level, Self::Error> {
        if let Some(sample) = self.samples.pop_front() {
            self.last = sample.ok_or(())?;
        }
        Ok(self.last)
    }
}

async fn verify_button<const BCM: u8>(
    pin: &ButtonPin<BCM>,
    expected_button: Button,
    samples: &[Option<Level>],
) {
    assert_eq!(pin.button(), expected_button);
    let mut firmware = Firmware::start().unwrap();
    let reader = SequenceReader {
        samples: samples.iter().copied().collect(),
        last: Level::High,
    };
    let _subscription = pin.start_subscription(reader, &firmware.events()).unwrap();

    let pressed = tokio::time::timeout(Duration::from_millis(200), firmware.after(0))
        .await
        .expect("button press should reach the runtime")
        .unwrap();
    assert_eq!(pressed.processed_events, 1, "{expected_button:?}");
    assert_eq!(
        pressed.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Pressed(expected_button)))
    );

    let released = tokio::time::timeout(Duration::from_millis(200), firmware.after(1))
        .await
        .expect("button release should reach the runtime")
        .unwrap();
    assert_eq!(released.processed_events, 2, "{expected_button:?}");
    assert_eq!(released.selected_index, pressed.selected_index);
    assert_eq!(released.menu_depth, pressed.menu_depth);
    assert_eq!(
        released.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Released(
            expected_button
        )))
    );

    // Held levels must not produce repeated button events.
    tokio::time::sleep(Duration::from_millis(50)).await;
    assert_eq!(
        firmware.snapshot().processed_events,
        2,
        "{expected_button:?}"
    );
    firmware.shutdown().await.unwrap();
}

#[tokio::test(start_paused = true)]
async fn every_panel_button_debounces_press_and_release_through_the_runtime() {
    use Level::{High, Low};

    // Five 5-ms samples at one level complete the 20-ms debounce period.
    let mut samples = vec![Some(High)]; // Initially unpressed.
    samples.extend([Some(Low), Some(High)]); // Press bounces and resets.
    samples.extend([Some(Low); 5]); // Stable press.
    samples.extend([Some(High), Some(Low)]); // Release bounces and resets.
    samples.extend([Some(High); 5]); // Stable release.

    let pins = BoardPins::get().gpio;
    verify_button(&pins.up_button, Button::Up, &samples).await;
    verify_button(&pins.down_button, Button::Down, &samples).await;
    verify_button(&pins.left_button, Button::Left, &samples).await;
    verify_button(&pins.right_button, Button::Right, &samples).await;
    verify_button(&pins.ok_button, Button::Ok, &samples).await;
    verify_button(&pins.reset_button, Button::Reset, &samples).await;
    verify_button(&pins.pass_button, Button::Pass, &samples).await;
    verify_button(&pins.function_one_button, Button::F1, &samples).await;
    verify_button(&pins.function_two_button, Button::F2, &samples).await;
    verify_button(&pins.function_three_button, Button::F3, &samples).await;
    verify_button(&pins.function_four_button, Button::F4, &samples).await;
    verify_button(&pins.function_five_button, Button::F5, &samples).await;
}

#[tokio::test(start_paused = true)]
async fn initially_held_button_does_not_invent_a_press() {
    use Level::{High, Low};

    let pin = BoardPins::get().gpio.down_button;
    let mut firmware = Firmware::start().unwrap();
    let reader = SequenceReader {
        samples: [
            Some(Low),
            Some(Low),
            Some(Low),
            Some(Low),
            Some(Low),
            Some(High),
            Some(High),
            Some(High),
            Some(High),
            Some(High),
            Some(Low),
            Some(Low),
            Some(Low),
            Some(Low),
            Some(Low),
        ]
        .into(),
        last: High,
    };
    let _subscription = pin.start_subscription(reader, &firmware.events()).unwrap();

    let released = tokio::time::timeout(Duration::from_millis(200), firmware.after(0))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(released.processed_events, 1);
    assert_eq!(released.selected_index, 0);
    assert_eq!(
        released.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Released(pin.button())))
    );

    let pressed = tokio::time::timeout(Duration::from_millis(200), firmware.after(1))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(pressed.selected_index, 1);
    assert_eq!(pressed.processed_events, 2);
    assert_eq!(
        pressed.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Pressed(pin.button())))
    );
    firmware.shutdown().await.unwrap();
}

#[tokio::test(start_paused = true)]
async fn failed_gpio_reads_do_not_prevent_later_press_and_release() {
    use Level::{High, Low};

    let samples = [
        Some(High),
        Some(Low),
        Some(Low),
        None, // A read fails while the press is settling.
        Some(Low),
        Some(Low),
        Some(Low),
        Some(Low),
        Some(Low),
        Some(High),
        Some(High),
        None, // A read fails while the release is settling.
        Some(High),
        Some(High),
        Some(High),
        Some(High),
        Some(High),
    ];
    verify_button(&BoardPins::get().gpio.down_button, Button::Down, &samples).await;
}
