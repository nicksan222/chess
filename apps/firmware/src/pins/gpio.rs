use core::marker::PhantomData;

use crate::events::Button;

mod button;

pub use button::{ButtonAction, ButtonPin, ButtonSubscription, StartSubscriptionError};

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
    pub(super) const fn get() -> Self {
        Self {
            up_button: ButtonPin::new(Button::Previous),
            down_button: ButtonPin::new(Button::Next),
            left_button: ButtonPin::new(Button::Back),
            right_button: ButtonPin::new(Button::Forward),
            ok_button: ButtonPin::new(Button::Confirm),
            reset_button: ButtonPin::new(Button::Reset),
            pass_button: ButtonPin::new(Button::Pass),
            function_one_button: ButtonPin::new(Button::FunctionOne),
            function_two_button: ButtonPin::new(Button::FunctionTwo),
            function_three_button: ButtonPin::new(Button::FunctionThree),
            function_four_button: ButtonPin::new(Button::FunctionFour),
            function_five_button: ButtonPin::new(Button::FunctionFive),
        }
    }
}

pub struct Pin<const BCM: u8, Capability> {
    gpio: GPIO,
    capability: PhantomData<Capability>,
}

impl<const BCM: u8, Capability> Pin<BCM, Capability> {
    pub(super) const fn new() -> Self {
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
