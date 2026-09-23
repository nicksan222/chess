use std::{error::Error as StdError, fmt};

/// Authentication requested for a client connection.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Credentials {
    /// Network without link-layer authentication.
    Open,
    /// WPA2/WPA3 Personal authentication.
    Personal(Passphrase),
}

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
