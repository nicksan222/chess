//! Typed, presentation-agnostic Wi-Fi control.
//!
//! The public model contains no NetworkManager, D-Bus, command-line, menu, or
//! display types. [`Connectivity`] implements those requests through NetworkManager.

mod network_manager;

use std::{error::Error as StdError, fmt};

pub use network_manager::{Connectivity, Error};

/// A validated UTF-8 Wi-Fi network name.
#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Ssid(String);

impl Ssid {
    /// Validates the IEEE 802.11 maximum of 32 bytes.
    pub fn new(value: impl Into<String>) -> Result<Self, InvalidSsid> {
        let value = value.into();
        if value.is_empty() || value.len() > 32 || value.contains('\0') {
            Err(InvalidSsid)
        } else {
            Ok(Self(value))
        }
    }

    /// Returns the network name.
    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Error returned when an SSID cannot be represented by this product API.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InvalidSsid;

impl fmt::Display for InvalidSsid {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("SSID must contain between 1 and 32 bytes and no NUL")
    }
}

impl StdError for InvalidSsid {}

/// A validated WPA Personal passphrase.
#[derive(Clone, Eq, PartialEq)]
pub struct Passphrase(String);

impl Passphrase {
    /// Accepts 8–63 non-control bytes or a 64-digit hexadecimal PSK.
    pub fn new(value: impl Into<String>) -> Result<Self, InvalidPassphrase> {
        let value = value.into();
        let bytes = value.as_bytes();
        let text = (8..=63).contains(&bytes.len())
            && value.chars().all(|character| !character.is_control());
        let hexadecimal = bytes.len() == 64 && bytes.iter().all(u8::is_ascii_hexdigit);
        if text || hexadecimal {
            Ok(Self(value))
        } else {
            Err(InvalidPassphrase)
        }
    }

    pub(super) fn expose(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for Passphrase {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("Passphrase([REDACTED])")
    }
}

/// Error returned for an invalid WPA Personal passphrase.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InvalidPassphrase;

impl fmt::Display for InvalidPassphrase {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("WPA passphrase must contain 8–63 bytes or 64 hexadecimal digits")
    }
}

impl StdError for InvalidPassphrase {}

/// Authentication requested for a client connection.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Credentials {
    /// Network without link-layer authentication.
    Open,
    /// WPA2/WPA3 Personal authentication.
    Personal(Passphrase),
}

/// Security category advertised by an access point.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Security {
    /// No link-layer authentication.
    Open,
    /// WPA Personal authentication.
    Personal,
    /// Enterprise authentication, which this initial product flow cannot join.
    Enterprise,
}

/// One visible Wi-Fi network.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AccessPoint {
    /// Network name.
    pub ssid: Ssid,
    /// Signal strength from zero through one hundred.
    pub signal: u8,
    /// Advertised authentication category.
    pub security: Security,
    /// Whether this network is currently active.
    pub connected: bool,
    /// Whether NetworkManager already has a saved profile.
    pub known: bool,
}

/// Current client connection state.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Status {
    /// No active Wi-Fi client connection.
    Disconnected,
    /// Connected to the named network.
    Connected(Ssid),
}

/// Complete hotspot configuration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Hotspot {
    /// Network name advertised by the board.
    pub ssid: Ssid,
    /// WPA passphrase required by provisioning clients.
    pub passphrase: Passphrase,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn domain_values_validate_boundaries_and_redact_secrets() {
        assert!(Ssid::new("").is_err());
        assert!(Ssid::new("x".repeat(33)).is_err());
        assert!(Ssid::new("Home").is_ok());
        assert!(Passphrase::new("short").is_err());
        let passphrase = Passphrase::new("correct horse").unwrap();
        assert_eq!(format!("{passphrase:?}"), "Passphrase([REDACTED])");
    }
}
