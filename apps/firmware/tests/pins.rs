use std::{collections::VecDeque, time::Duration};

use firmware::events::EventEmitter;
use firmware::hardware::pins::{
    BoardPins, ButtonAction, ButtonPin, GPIO, InputOutput, Level, Output, Pin, ReadLevel, Readable,
    Writable, WriteLevel,
};

struct Lines {
    level: Level,
}

impl ReadLevel for Lines {
    type Error = ();

    fn read_level(&mut self, _: GPIO) -> Result<Level, Self::Error> {
        Ok(self.level)
    }
}

impl WriteLevel for Lines {
    type Error = ();

    fn write_level(&mut self, _: GPIO, level: Level) -> Result<(), Self::Error> {
        self.level = level;
        Ok(())
    }
}

#[test]
fn board_interfaces_use_the_hardware_bcm_numbers() {
    let pins = BoardPins::get();

    assert_eq!(
        [pins.i2c.data.bcm_number(), pins.i2c.clock.bcm_number()],
        [2, 3]
    );
    assert_eq!(
        [pins.spi.data.bcm_number(), pins.spi.clock.bcm_number()],
        [10, 11]
    );
    assert_eq!(
        [
            pins.gpio.up_button.bcm_number(),
            pins.gpio.down_button.bcm_number(),
            pins.gpio.left_button.bcm_number(),
            pins.gpio.right_button.bcm_number(),
            pins.gpio.ok_button.bcm_number(),
            pins.gpio.reset_button.bcm_number(),
            pins.gpio.pass_button.bcm_number(),
            pins.gpio.function_one_button.bcm_number(),
            pins.gpio.function_two_button.bcm_number(),
            pins.gpio.function_three_button.bcm_number(),
            pins.gpio.function_four_button.bcm_number(),
            pins.gpio.function_five_button.bcm_number(),
        ],
        [5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24]
    );
}

#[test]
fn capabilities_are_enforced_by_pin_types() {
    fn read<const BCM: u8, C: Readable>(_: &Pin<BCM, C>) {}
    fn write<const BCM: u8, C: Writable>(_: &Pin<BCM, C>) {}
    fn gpio(_: &ButtonPin<5>) {}
    fn i2c(_: &Pin<2, InputOutput>) {}
    fn spi(_: &Pin<10, Output>) {}

    let pins = BoardPins::get();

    read(&pins.i2c.data);
    write(&pins.spi.data);
    write(&pins.i2c.data);
    gpio(&pins.gpio.up_button);
    i2c(&pins.i2c.data);
    spi(&pins.spi.data);
}

#[test]
fn pins_read_and_write_levels() {
    let pins = BoardPins::get();
    let mut lines = Lines { level: Level::Low };

    assert_eq!(pins.gpio.up_button.read_level(&mut lines), Ok(Level::Low));
    pins.spi.data.set_level(&mut lines, Level::High).unwrap();
    assert_eq!(lines.level, Level::High);
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

#[test]
fn starting_a_button_subscription_without_a_runtime_returns_an_error() {
    let pins = BoardPins::get();
    let events = EventEmitter::new();
    let reader = Lines { level: Level::High };

    let error = pins
        .gpio
        .down_button
        .start_subscription(reader, &events)
        .unwrap_err();

    assert_eq!(
        error.to_string(),
        "button subscriptions require an active Tokio runtime"
    );
}

#[tokio::test(start_paused = true)]
async fn button_pins_poll_debounce_and_deliver_domain_actions() {
    let pins = BoardPins::get();
    let events = EventEmitter::new();
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
    let mut next = pins
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
