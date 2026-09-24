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
