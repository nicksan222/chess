//! Typed, presentation-agnostic Wi-Fi control.
//!
//! Product types stay independent from NetworkManager, D-Bus, menus, and displays;
//! [`Connectivity`] translates them to the maintained `nmrs` implementation.

mod access_point;
mod credentials;
mod hotspot;
mod network_manager;
mod ssid;
mod status;

pub use access_point::{AccessPoint, Security};
pub use credentials::{Credentials, InvalidPassphrase, Passphrase};
pub use hotspot::Hotspot;
pub use network_manager::{Connectivity, Error};
pub use ssid::{InvalidSsid, Ssid};
pub use status::Status;

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
