//! Typed, presentation-agnostic Wi-Fi control.
//!
//! Product types stay independent from NetworkManager, D-Bus, menus, and displays;
//! [`Connectivity`] translates them through an internal backend seam to the maintained
//! `nmrs` implementation, which tests replace with an in-memory fake.

mod access_point;
mod backend;
mod client;
mod credentials;
mod error;
#[cfg(test)]
mod fake;
mod hotspot;
mod network_manager;
mod ssid;
mod status;

pub use access_point::{AccessPoint, Security};
pub use client::Connectivity;
pub use credentials::{Credentials, InvalidPassphrase, Passphrase};
pub use error::Error;
pub use hotspot::Hotspot;
pub use ssid::{InvalidSsid, Ssid};
pub use status::Status;
