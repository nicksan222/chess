use embedded_hal::i2c::{self, ErrorKind};
use std::{fmt, io};

/// A Linux I2C failure, retaining its operating-system cause.
#[derive(Debug)]
pub struct LinuxI2cError(pub(super) io::Error);

impl i2c::Error for LinuxI2cError {
    fn kind(&self) -> ErrorKind {
        ErrorKind::Other
    }
}
impl fmt::Display for LinuxI2cError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}
impl std::error::Error for LinuxI2cError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        Some(&self.0)
    }
}
