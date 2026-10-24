use super::{Passphrase, Ssid};

/// Complete provisioning hotspot configuration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Hotspot {
    /// Network name advertised by the board.
    pub ssid: Ssid,
    /// WPA passphrase required by provisioning clients.
    pub passphrase: Passphrase,
}
