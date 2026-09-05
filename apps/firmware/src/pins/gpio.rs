use core::marker::PhantomData;

use super::Gpio;

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

    fn read_level(&mut self, gpio: Gpio) -> Result<Level, Self::Error>;
}

/// Writes electrical levels to GPIOs.
pub trait WriteLevel {
    type Error;

    fn write_level(&mut self, gpio: Gpio, level: Level) -> Result<(), Self::Error>;
}

pub struct Pin<const BCM: u8, Capability> {
    gpio: Gpio,
    capability: PhantomData<Capability>,
}

impl<const BCM: u8, Capability> Pin<BCM, Capability> {
    pub(super) const fn new(gpio: Gpio) -> Self {
        assert!(gpio.bcm_number() == BCM, "GPIO and BCM number differ");
        Self {
            gpio,
            capability: PhantomData,
        }
    }

    pub const fn gpio(&self) -> Gpio {
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
