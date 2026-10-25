use std::{fmt, io};

use embedded_hal::i2c::{self, ErrorKind, NoAcknowledgeSource};

/// An `i2c-dev` failure, keeping the operating-system cause.
#[derive(Debug)]
pub struct LinuxI2cError(pub(super) io::Error);

impl i2c::Error for LinuxI2cError {
    fn kind(&self) -> ErrorKind {
        // i2c-dev drivers report an unacknowledged address as ENXIO or EREMOTEIO.
        match self.0.raw_os_error() {
            Some(libc::ENXIO | libc::EREMOTEIO) => {
                ErrorKind::NoAcknowledge(NoAcknowledgeSource::Unknown)
            }
            Some(libc::EAGAIN) => ErrorKind::ArbitrationLoss,
            _ => ErrorKind::Other,
        }
    }
}

impl fmt::Display for LinuxI2cError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

impl std::error::Error for LinuxI2cError {}

#[cfg(test)]
mod tests {
    use embedded_hal::i2c::Error;

    use super::*;

    fn kind(code: i32) -> ErrorKind {
        LinuxI2cError(io::Error::from_raw_os_error(code)).kind()
    }

    #[test]
    fn unacknowledged_transfers_map_to_no_acknowledge() {
        for code in [libc::ENXIO, libc::EREMOTEIO] {
            assert_eq!(
                kind(code),
                ErrorKind::NoAcknowledge(NoAcknowledgeSource::Unknown)
            );
        }
        assert_eq!(kind(libc::EAGAIN), ErrorKind::ArbitrationLoss);
        assert_eq!(kind(libc::EIO), ErrorKind::Other);
    }
}
