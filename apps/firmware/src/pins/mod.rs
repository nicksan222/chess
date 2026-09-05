//! Board interfaces connected through the Raspberry Pi GPIO header.

mod gpio;
mod i2c;
mod spi;

pub use gpio::{
    GPIO, GPIOPins, Input, InputOutput, Level, Output, Pin, ReadLevel, Readable, Writable,
    WriteLevel,
};
pub use i2c::I2cPins;
pub use spi::SpiPins;

/// The only three host interfaces connected by the board hardware.
pub struct BoardPins {
    pub gpio: GPIOPins,
    pub i2c: I2cPins,
    pub spi: SpiPins,
}

impl BoardPins {
    pub const fn get() -> Self {
        Self {
            gpio: GPIOPins::get(),
            i2c: I2cPins::get(),
            spi: SpiPins::get(),
        }
    }
}
