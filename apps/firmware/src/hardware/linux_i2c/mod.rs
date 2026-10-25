//! `embedded-hal` I2C over a Linux `i2c-dev` character device.
//!
//! Each transaction is one `I2C_RDWR` ioctl, so the kernel joins its messages
//! with repeated starts and ends it with a single stop.

mod error;
mod plan;

use i2cdev::{core::I2CTransfer, linux::LinuxI2CBus};
use std::{io, path::Path};

use embedded_hal::i2c::{ErrorType, I2c, Operation};

pub use error::LinuxI2cError;
use plan::Plan;

/// An open I2C bus such as `/dev/i2c-1`.
#[derive(Debug)]
pub struct LinuxI2c {
    device: LinuxI2CBus,
}

impl LinuxI2c {
    /// Opens the Linux I2C character device.
    ///
    /// # Errors
    /// Returns the operating-system error if the device cannot be opened.
    pub fn open(path: impl AsRef<Path>) -> io::Result<Self> {
        let device = LinuxI2CBus::new(path).map_err(io::Error::from)?;
        Ok(Self { device })
    }

    fn completed(result: u32, expected: usize) -> Result<(), LinuxI2cError> {
        if usize::try_from(result).ok() != Some(expected) {
            return Err(LinuxI2cError(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                format!("I2C transfer completed {result} of {expected} messages"),
            )));
        }
        Ok(())
    }
}

impl ErrorType for LinuxI2c {
    type Error = LinuxI2cError;
}

impl I2c for LinuxI2c {
    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [Operation<'_>],
    ) -> Result<(), Self::Error> {
        let mut plan = Plan::new(operations);
        if plan.is_empty() {
            return Ok(());
        }
        let mut messages = plan.messages(address)?;
        let completed = self
            .device
            .transfer(&mut messages)
            .map_err(|error| LinuxI2cError(io::Error::from(error)))?;
        Self::completed(completed, messages.len())?;
        plan.scatter(operations);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn short_transfers_are_errors_instead_of_successful_zero_filled_reads() {
        for completed in [0, 1] {
            assert!(LinuxI2c::completed(completed, 2).is_err());
        }
        assert!(LinuxI2c::completed(2, 2).is_ok());
    }

    #[test]
    fn a_missing_bus_fails_to_open() {
        let error = LinuxI2c::open("/dev/i2c-does-not-exist").err().unwrap();
        assert_eq!(error.kind(), io::ErrorKind::NotFound);
    }
}
