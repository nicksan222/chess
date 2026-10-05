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

#[cfg(test)]
mod tests {
    use super::Passphrase;

    #[test]
    fn passphrase_validation_and_debug_redaction() {
        assert!(Passphrase::new("short").is_err());
        assert!(Passphrase::new("abcdefgh\n").is_err()); // Control character.
        assert!(Passphrase::new("a".repeat(65)).is_err());
        assert!(Passphrase::new("g".repeat(64)).is_err()); // Not hexadecimal.

        for valid in ["12345678".to_owned(), "a".repeat(63), "f".repeat(64)] {
            let passphrase = Passphrase::new(valid.clone()).unwrap();
            assert_eq!(format!("{passphrase:?}"), "Passphrase([REDACTED])");
            assert!(!format!("{passphrase:?}").contains(&valid));
        }
    }

    #[test]
    fn length_boundaries_are_inclusive_and_empty_is_rejected() {
        assert!(Passphrase::new("").is_err());
        assert!(Passphrase::new("1234567").is_err()); // 7
        assert!(Passphrase::new("12345678").is_ok()); // 8
        assert!(Passphrase::new("a".repeat(63)).is_ok());
        assert!(Passphrase::new("g".repeat(64)).is_err()); // 64 but not hexadecimal
        assert!(Passphrase::new("a".repeat(64)).is_ok()); // 64 hexadecimal digits
        assert!(Passphrase::new("A".repeat(64)).is_ok()); // uppercase hexadecimal
        assert!(Passphrase::new("0".repeat(65)).is_err());
    }

    #[test]
    fn length_counts_bytes_not_characters() {
        assert!(Passphrase::new("é".repeat(4)).is_ok()); // 4 characters, 8 bytes.
        assert!(Passphrase::new("é".repeat(3)).is_err()); // 6 bytes.
        assert!(Passphrase::new("€".repeat(21)).is_ok()); // 63 bytes.
        assert!(Passphrase::new("€".repeat(22)).is_err()); // 66 bytes.
    }

    #[test]
    fn control_characters_are_rejected_anywhere_including_c1_and_tab() {
        for bad in ["abcdefg\u{7f}", "abc\tdefgh", "\0abcdefgh", "abcdefg\u{85}"] {
            assert!(Passphrase::new(bad).is_err(), "{bad:?}");
        }
        assert!(Passphrase::new("pass phrase!").is_ok()); // Spaces are fine.
    }

    #[test]
    fn invalid_passphrase_explains_the_constraint() {
        assert_eq!(
            Passphrase::new("x").unwrap_err().to_string(),
            "WPA passphrase must contain 8–63 bytes or 64 hexadecimal digits"
        );
    }

    #[test]
    fn secrets_do_not_leak_through_containing_types_debug_output() {
        use crate::connectivity::{Credentials, Hotspot, Ssid};

        let secret = "hunter2-hunter2";
        let credentials = Credentials::Personal(Passphrase::new(secret).unwrap());
        assert!(!format!("{credentials:?}").contains(secret));
        let hotspot = Hotspot {
            ssid: Ssid::new("Setup").unwrap(),
            passphrase: Passphrase::new(secret).unwrap(),
        };
        let shown = format!("{hotspot:?} {:#?}", hotspot.clone());
        assert!(!shown.contains(secret));
        assert!(shown.contains("Setup"));
    }
}
