use std::{error::Error as StdError, fmt};

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

#[cfg(test)]
mod tests {
    use super::Ssid;

    #[test]
    fn ssid_validation_uses_utf8_bytes_and_rejects_nul() {
        assert!(Ssid::new("").is_err());
        assert!(Ssid::new("a\0b").is_err());
        assert!(Ssid::new("é".repeat(17)).is_err()); // 34 bytes, not 17.
        assert!(Ssid::new("é".repeat(16)).is_ok()); // Exactly 32 bytes.
        assert!(Ssid::new("a".repeat(32)).is_ok());
        assert_eq!(Ssid::new("Home").unwrap().as_str(), "Home");
    }
}
