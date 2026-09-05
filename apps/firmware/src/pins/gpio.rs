use core::marker::PhantomData;

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

pub struct Input;
pub struct Output;
pub struct InputOutput;

pub trait Readable {}
pub trait Writable {}

impl Readable for Input {}
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
    pub up_button: Pin<5, Input>,
    pub down_button: Pin<6, Input>,
    pub left_button: Pin<12, Input>,
    pub right_button: Pin<13, Input>,
    pub ok_button: Pin<16, Input>,
    pub reset_button: Pin<17, Input>,
    pub pass_button: Pin<19, Input>,
    pub function_one_button: Pin<20, Input>,
    pub function_two_button: Pin<21, Input>,
    pub function_three_button: Pin<22, Input>,
    pub function_four_button: Pin<23, Input>,
    pub function_five_button: Pin<24, Input>,
}

impl GPIOPins {
    pub(super) const fn get() -> Self {
        Self {
            up_button: Pin::new(GPIO::new(5)),
            down_button: Pin::new(GPIO::new(6)),
            left_button: Pin::new(GPIO::new(12)),
            right_button: Pin::new(GPIO::new(13)),
            ok_button: Pin::new(GPIO::new(16)),
            reset_button: Pin::new(GPIO::new(17)),
            pass_button: Pin::new(GPIO::new(19)),
            function_one_button: Pin::new(GPIO::new(20)),
            function_two_button: Pin::new(GPIO::new(21)),
            function_three_button: Pin::new(GPIO::new(22)),
            function_four_button: Pin::new(GPIO::new(23)),
            function_five_button: Pin::new(GPIO::new(24)),
        }
    }
}

pub struct Pin<const BCM: u8, Capability> {
    gpio: GPIO,
    capability: PhantomData<Capability>,
}

impl<const BCM: u8, Capability> Pin<BCM, Capability> {
    pub(super) const fn new(gpio: GPIO) -> Self {
        assert!(gpio.bcm_number() == BCM, "GPIO and BCM number differ");
        Self {
            gpio,
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
