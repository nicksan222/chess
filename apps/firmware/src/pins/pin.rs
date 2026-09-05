use core::marker::PhantomData;

use super::{Capability, CapabilityKind, Gpio, Level, OutputBackend, Writable};

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

impl<const BCM: u8, C: Writable> Pin<BCM, C> {
    /// Drives the line to an explicit electrical level.
    pub fn set_level<B: OutputBackend>(
        &self,
        backend: &mut B,
        level: Level,
    ) -> Result<(), B::Error> {
        backend.set_level(self.gpio, level)
    }

    pub fn set_high<B: OutputBackend>(&self, backend: &mut B) -> Result<(), B::Error> {
        self.set_level(backend, Level::High)
    }

    pub fn set_low<B: OutputBackend>(&self, backend: &mut B) -> Result<(), B::Error> {
        self.set_level(backend, Level::Low)
    }

    /// Asserts the pin's logical function, accounting for active-low wiring.
    pub fn turn_on<B: OutputBackend>(&self, backend: &mut B) -> Result<(), B::Error> {
        self.set_level(
            backend,
            if self.is_active_low() {
                Level::Low
            } else {
                Level::High
            },
        )
    }

    /// Deasserts the pin's logical function, accounting for active-low wiring.
    pub fn turn_off<B: OutputBackend>(&self, backend: &mut B) -> Result<(), B::Error> {
        self.set_level(
            backend,
            if self.is_active_low() {
                Level::High
            } else {
                Level::Low
            },
        )
    }
}
