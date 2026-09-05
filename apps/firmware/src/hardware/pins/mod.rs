#![allow(clippy::upper_case_acronyms)]

//! Board interfaces connected through the Raspberry Pi GPIO header.
//!
//! Hardware interface names retain their schematic spellings (`GPIO`, `I2C`,
//! and `SPI`) throughout this API.

mod gpio;
mod i2c;
mod spi;

pub use gpio::{
    ButtonAction, ButtonPin, ButtonSubscription, GPIO, GPIOPins, InputOutput, Level, Output, Pin,
    ReadLevel, Readable, StartSubscriptionError, Writable, WriteLevel,
};
pub use i2c::I2CPins;
pub use spi::SPIPins;

/// The only three host interfaces connected by the board hardware.
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
