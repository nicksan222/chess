#![allow(dead_code)]

#[path = "../src/pins/mod.rs"]
mod pins;

use pins::{BoardPins, Gpio, InputOutput, Level, Pin, ReadLevel, Readable, Writable, WriteLevel};

struct Lines {
    level: Level,
}

impl ReadLevel for Lines {
    type Error = ();

    fn read_level(&mut self, _: Gpio) -> Result<Level, Self::Error> {
        Ok(self.level)
    }
}

impl WriteLevel for Lines {
    type Error = ();

    fn write_level(&mut self, _: Gpio, level: Level) -> Result<(), Self::Error> {
        self.level = level;
        Ok(())
    }
}

#[test]
fn gpio_values_are_bcm_numbers() {
    assert_eq!(Gpio::I2cData.bcm_number(), 2);
    assert_eq!(Gpio::UpButton.bcm_number(), 5);
    assert_eq!(Gpio::LedData.bcm_number(), 10);
}

#[test]
fn capabilities_are_enforced_by_pin_types() {
    fn read<const BCM: u8, C: Readable>(_: &Pin<BCM, C>) {}
    fn write<const BCM: u8, C: Writable>(_: &Pin<BCM, C>) {}
    fn i2c(_: &Pin<2, InputOutput>) {}

    let pins = BoardPins::get();

    read(&pins.up_button);
    read(&pins.i2c_data);
    write(&pins.led_data);
    write(&pins.i2c_data);
    i2c(&pins.i2c_data);
}

#[test]
fn pins_read_and_write_levels() {
    let pins = BoardPins::get();
    let mut lines = Lines { level: Level::Low };

    assert_eq!(pins.up_button.read_level(&mut lines), Ok(Level::Low));
    pins.led_data.set_level(&mut lines, Level::High).unwrap();
    assert_eq!(lines.level, Level::High);
}
