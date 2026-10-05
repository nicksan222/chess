//! Failure type returned by connectivity operations.

use std::fmt;

use super::InvalidSsid;

/// Failure returned by connectivity operations.
#[derive(Debug)]
pub enum Error {
    /// The D-Bus client or NetworkManager rejected an operation.
    NetworkManager(Box<nmrs::ConnectionError>),
    /// NetworkManager returned an SSID outside the product model's constraints.
    InvalidSsid(InvalidSsid),
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NetworkManager(error) => write!(formatter, "NetworkManager failed: {error}"),
            Self::InvalidSsid(error) => error.fmt(formatter),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::NetworkManager(error) => Some(error),
            Self::InvalidSsid(error) => Some(error),
        }
    }
}

impl From<nmrs::ConnectionError> for Error {
    fn from(error: nmrs::ConnectionError) -> Self {
        Self::NetworkManager(Box::new(error))
    }
}
