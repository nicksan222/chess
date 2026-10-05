//! The system operations [`Connectivity`](super::Connectivity) needs from a Wi-Fi stack.
//!
//! The trait is the seam between product logic (SSID validation, security
//! classification, sorting, hotspot bookkeeping) and the operating system. The
//! production implementation talks to NetworkManager; tests substitute an
//! in-memory one. The module is private to the crate, so the trait is not part
//! of the public API.

use super::{Credentials, Error, Hotspot, Ssid};

/// A network as reported by the Wi-Fi stack, before product validation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VisibleNetwork {
    /// Raw network name; may not satisfy [`Ssid`]'s constraints.
    pub ssid: String,
    /// Signal strength from zero through one hundred, when reported.
    pub strength: Option<u8>,
    /// Whether any authentication is advertised.
    pub secured: bool,
    /// Whether the advertised authentication is enterprise (802.1X).
    pub enterprise: bool,
    /// Whether this network is the active connection.
    pub active: bool,
    /// Whether a saved profile exists.
    pub known: bool,
}

/// Wi-Fi operations on the board's radio.
///
/// Used only through generics inside this crate, so each future's `Send`-ness is
/// checked on the concrete backend rather than promised by the trait.
#[allow(async_fn_in_trait)]
pub trait WifiBackend {
    /// SSID of the active client connection, if any.
    async fn current_ssid(&self) -> Option<String>;
    /// Requests a fresh scan, then lists the visible networks (unsorted).
    async fn scan(&self) -> Result<Vec<VisibleNetwork>, Error>;
    /// Removes the saved profile and any active connection for `ssid`.
    async fn forget(&self, ssid: &str) -> Result<(), Error>;
    /// Creates and activates a WPA2 access point with shared IPv4 addressing.
    async fn start_access_point(&self, hotspot: &Hotspot) -> Result<(), Error>;
    /// Joins an open or WPA Personal network as a client.
    async fn join(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error>;
}
