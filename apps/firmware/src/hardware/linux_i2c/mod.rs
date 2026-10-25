//! `embedded-hal` I2C over a Linux `i2c-dev` character device.
//!
//! Each transaction is one `I2C_RDWR` ioctl, so the kernel joins its messages
//! with repeated starts and ends it with a single stop.

mod error;
mod ffi;
mod plan;

use std::{fs::File, io, os::fd::AsRawFd, path::Path};

use embedded_hal::i2c::{ErrorType, I2c, Operation};

pub use error::LinuxI2cError;
use ffi::{I2C_RDWR, Message, Transfer};
use plan::Plan;

/// An open I2C bus such as `/dev/i2c-1`.
pub struct LinuxI2c {
    device: File,
}

impl LinuxI2c {
    pub fn open(path: impl AsRef<Path>) -> io::Result<Self> {
        let device = File::options().read(true).write(true).open(path)?;
        Ok(Self { device })
    }

    /// Performs `messages` as one combined transfer.
    fn transfer(&self, messages: &mut [Message]) -> Result<(), LinuxI2cError> {
        let mut transfer = Transfer {
            messages: messages.as_mut_ptr(),
            // At most one message per operation, and operations fit in memory.
            count: messages.len() as u32,
        };
        // SAFETY: `transfer` describes `messages`, whose buffers the caller
        // keeps alive and sized to their lengths for the duration of the call.
        let result = unsafe { libc::ioctl(self.device.as_raw_fd(), I2C_RDWR, &mut transfer) };
        Self::completed(result, messages.len())
    }

    fn completed(result: libc::c_int, expected: usize) -> Result<(), LinuxI2cError> {
        if result < 0 {
            return Err(LinuxI2cError(io::Error::last_os_error()));
        }
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
        self.transfer(&mut messages)?;
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
