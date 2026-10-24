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
pub(super) struct VisibleNetwork {
    /// Raw network name; may not satisfy [`Ssid`]'s constraints.
    pub(super) ssid: String,
    /// Signal strength from zero through one hundred, when reported.
    pub(super) strength: Option<u8>,
    /// Whether any authentication is advertised.
    pub(super) secured: bool,
    /// Whether the advertised authentication is enterprise (802.1X).
    pub(super) enterprise: bool,
    /// Whether this network is the active connection.
    pub(super) active: bool,
    /// Whether a saved profile exists.
    pub(super) known: bool,
}

/// What the Wi-Fi stack reports about the board's radio.
#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) enum Radio {
    /// Confirmed idle: enabled but not connected, or disabled.
    Disconnected,
    /// Connecting, authenticating, configuring addresses or disconnecting.
    Changing,
    /// Active, with the SSID of its connection when one is reported.
    Active { ssid: Option<String> },
    /// In a state the product cannot interpret, such as unmanaged or failed.
    Unknown,
}

/// Wi-Fi operations on the board's radio.
///
/// Used only through generics inside this crate, so each future's `Send`-ness is
/// checked on the concrete backend rather than promised by the trait.
#[allow(async_fn_in_trait)]
pub(super) trait WifiBackend {
    /// The radio's current state; a failed query is an error, never a state.
    async fn radio(&self) -> Result<Radio, Error>;
    /// Requests a fresh scan, then lists the visible networks (unsorted).
    async fn scan(&self) -> Result<Vec<VisibleNetwork>, Error>;
    /// Removes the saved profile and any active connection for `ssid`.
    async fn forget(&self, ssid: &str) -> Result<(), Error>;
    /// Creates and activates a WPA2 access point with shared IPv4 addressing.
    async fn start_access_point(&self, hotspot: &Hotspot) -> Result<(), Error>;
    /// Joins an open or WPA Personal network as a client.
    async fn join(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error>;
}
