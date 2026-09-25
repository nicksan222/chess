//! Board wiring, GPIO identities, and capability-checked pin access.
//!
//! These descriptors contain no Linux device handles; the OS adapter lives in
//! `hardware::linux_gpio` and button polling lives in `hardware::buttons`.

use core::marker::PhantomData;

pub use super::buttons::{
    Button, ButtonAction, ButtonEvent, ButtonPin, ButtonSubscription, StartSubscriptionError,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[allow(clippy::upper_case_acronyms)]
pub struct GPIO(u8);

impl GPIO {
    pub(super) const fn new(bcm_number: u8) -> Self {
        Self(bcm_number)
    }

    pub const fn bcm_number(self) -> u8 {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Level {
    Low,
    High,
}

pub struct Output;
pub struct InputOutput;

pub trait Readable {}
pub trait Writable {}

impl Readable for InputOutput {}
impl Writable for Output {}
impl Writable for InputOutput {}

/// Reads electrical levels from GPIOs.
pub trait ReadLevel {
    type Error;

    fn read_level(&mut self, gpio: GPIO) -> Result<Level, Self::Error>;
}

/// Writes electrical levels to GPIOs.
pub trait WriteLevel {
    type Error;

    fn write_level(&mut self, gpio: GPIO, level: Level) -> Result<(), Self::Error>;
}

pub struct Pin<const BCM: u8, Capability> {
    gpio: GPIO,
    capability: PhantomData<Capability>,
}

impl<const BCM: u8, Capability> Pin<BCM, Capability> {
    const fn new() -> Self {
        Self {
            gpio: GPIO::new(BCM),
            capability: PhantomData,
        }
    }

    pub const fn gpio(&self) -> GPIO {
        self.gpio
    }

    pub const fn bcm_number(&self) -> u8 {
        BCM
    }
}

impl<const BCM: u8, Capability: Readable> Pin<BCM, Capability> {
    pub fn read_level<R: ReadLevel>(&self, reader: &mut R) -> Result<Level, R::Error> {
        reader.read_level(self.gpio)
    }
}

impl<const BCM: u8, Capability: Writable> Pin<BCM, Capability> {
    pub fn set_level<W: WriteLevel>(&self, writer: &mut W, level: Level) -> Result<(), W::Error> {
        writer.write_level(self.gpio, level)
    }
}

/// Direct high/low GPIO pins used by the control-panel buttons.
pub struct GPIOPins {
    pub up_button: ButtonPin<5>,
    pub down_button: ButtonPin<6>,
    pub left_button: ButtonPin<12>,
    pub right_button: ButtonPin<13>,
    pub ok_button: ButtonPin<16>,
    pub reset_button: ButtonPin<17>,
    pub pass_button: ButtonPin<19>,
    pub function_one_button: ButtonPin<20>,
    pub function_two_button: ButtonPin<21>,
    pub function_three_button: ButtonPin<22>,
    pub function_four_button: ButtonPin<23>,
    pub function_five_button: ButtonPin<24>,
}

impl GPIOPins {
    const fn get() -> Self {
        Self {
            up_button: ButtonPin::new(Button::Up),
            down_button: ButtonPin::new(Button::Down),
            left_button: ButtonPin::new(Button::Left),
            right_button: ButtonPin::new(Button::Right),
            ok_button: ButtonPin::new(Button::Ok),
            reset_button: ButtonPin::new(Button::Reset),
            pass_button: ButtonPin::new(Button::Pass),
            function_one_button: ButtonPin::new(Button::F1),
            function_two_button: ButtonPin::new(Button::F2),
            function_three_button: ButtonPin::new(Button::F3),
            function_four_button: ButtonPin::new(Button::F4),
            function_five_button: ButtonPin::new(Button::F5),
        }
    }
}

/// Pins for the board's shared I2C bus.
pub struct I2CPins {
    pub data: Pin<2, InputOutput>,
    pub clock: Pin<3, InputOutput>,
}

impl I2CPins {
    const fn get() -> Self {
        Self {
            data: Pin::new(),
            clock: Pin::new(),
        }
    }
}

/// Pins for the SPI LED chain.
pub struct SPIPins {
    pub data: Pin<10, Output>,
    pub clock: Pin<11, Output>,
}

impl SPIPins {
    const fn get() -> Self {
        Self {
            data: Pin::new(),
            clock: Pin::new(),
        }
    }
}

/// The three host interfaces connected by the board hardware.
pub struct BoardPins {
    pub gpio: GPIOPins,
    pub i2c: I2CPins,
    pub spi: SPIPins,
}

impl BoardPins {
    pub const fn get() -> Self {
        Self {
            gpio: GPIOPins::get(),
            i2c: I2CPins::get(),
            spi: SPIPins::get(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
        let gpio = pins.gpio;
        assert_eq!(
            [
                (gpio.up_button.bcm_number(), gpio.up_button.button()),
                (gpio.down_button.bcm_number(), gpio.down_button.button()),
                (gpio.left_button.bcm_number(), gpio.left_button.button()),
                (gpio.right_button.bcm_number(), gpio.right_button.button()),
                (gpio.ok_button.bcm_number(), gpio.ok_button.button()),
                (gpio.reset_button.bcm_number(), gpio.reset_button.button()),
                (gpio.pass_button.bcm_number(), gpio.pass_button.button()),
                (
                    gpio.function_one_button.bcm_number(),
                    gpio.function_one_button.button()
                ),
                (
                    gpio.function_two_button.bcm_number(),
                    gpio.function_two_button.button()
                ),
                (
                    gpio.function_three_button.bcm_number(),
                    gpio.function_three_button.button()
                ),
                (
                    gpio.function_four_button.bcm_number(),
                    gpio.function_four_button.button()
                ),
                (
                    gpio.function_five_button.bcm_number(),
                    gpio.function_five_button.button()
                ),
            ],
            [
                (5, Button::Up),
                (6, Button::Down),
                (12, Button::Left),
                (13, Button::Right),
                (16, Button::Ok),
                (17, Button::Reset),
                (19, Button::Pass),
                (20, Button::F1),
                (21, Button::F2),
                (22, Button::F3),
                (23, Button::F4),
                (24, Button::F5),
            ]
        );
    }

    #[test]
    fn capabilities_are_enforced_by_pin_types() {
        fn read<const BCM: u8, C: Readable>(_: &Pin<BCM, C>) {}
        fn write<const BCM: u8, C: Writable>(_: &Pin<BCM, C>) {}
        fn button(_: &ButtonPin<5>) {}
        fn i2c(_: &Pin<2, InputOutput>) {}
        fn spi(_: &Pin<10, Output>) {}

        let pins = BoardPins::get();
        read(&pins.i2c.data);
        write(&pins.spi.data);
        write(&pins.i2c.data);
        button(&pins.gpio.up_button);
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
}
