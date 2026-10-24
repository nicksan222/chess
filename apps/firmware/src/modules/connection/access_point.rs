use super::Ssid;

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

/// Product-level security category advertised by an access point.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Security {
    /// No link-layer authentication.
    Open,
    /// WPA Personal authentication.
    Personal,
    /// Enterprise authentication, which this product flow cannot join.
    Enterprise,
}
