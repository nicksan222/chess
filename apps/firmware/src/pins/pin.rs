//! Generic, capability-checked GPIO pins.

use core::marker::PhantomData;

use super::Gpio;

/// Runtime representation of a pin's compile-time capability.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum CapabilityKind {
    Input,
    Output,
    InputOutput,
}

impl CapabilityKind {
    pub const fn can_read(self) -> bool {
        matches!(self, Self::Input | Self::InputOutput)
    }

    pub const fn can_write(self) -> bool {
        matches!(self, Self::Output | Self::InputOutput)
    }
}

/// Associates a mode marker with its runtime representation.
pub trait Capability {
    const KIND: CapabilityKind;
}

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Input;

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Output;

#[derive(Debug, Eq, Hash, PartialEq)]
pub struct InputOutput;

impl Capability for Input {
    const KIND: CapabilityKind = CapabilityKind::Input;
}

impl Capability for Output {
    const KIND: CapabilityKind = CapabilityKind::Output;
}

impl Capability for InputOutput {
    const KIND: CapabilityKind = CapabilityKind::InputOutput;
}

/// Implemented by modes that may be sampled.
pub trait Readable: Capability {}

/// Implemented by modes that may be driven.
pub trait Writable: Capability {}

impl Readable for Input {}
impl Readable for InputOutput {}
impl Writable for Output {}
impl Writable for InputOutput {}

/// A GPIO whose BCM number and capability are part of its type.
#[derive(Debug, Eq, Hash, PartialEq)]
pub struct Pin<const BCM: u8, C: Capability> {
    gpio: Gpio,
    mode: PhantomData<C>,
}

impl<const BCM: u8, C: Capability> Pin<BCM, C> {
    pub(super) const fn new(gpio: Gpio) -> Self {
        assert!(BCM <= 27, "invalid Raspberry Pi Zero GPIO number");
        assert!(gpio.bcm_number() == BCM, "GPIO and BCM number differ");
        assert!(
            gpio.capability() as u8 == C::KIND as u8,
            "GPIO mode differs"
        );

        Self {
            gpio,
            mode: PhantomData,
        }
    }

    pub const fn gpio(&self) -> Gpio {
        self.gpio
    }

    pub const fn name(&self) -> &'static str {
        self.gpio.name()
    }

    pub const fn bcm_number(&self) -> u8 {
        BCM
    }

    pub const fn header_pin(&self) -> u8 {
        self.gpio.header_pin()
    }

    pub const fn capability(&self) -> CapabilityKind {
        C::KIND
    }

    pub const fn is_active_low(&self) -> bool {
        self.gpio.is_active_low()
    }
}
