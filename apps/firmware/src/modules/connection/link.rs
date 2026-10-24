use super::Ssid;

/// Current client connection state.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Link {
    /// No active Wi-Fi client connection: the radio is idle or switched off.
    Disconnected,
    /// The radio is connecting or disconnecting.
    Changing,
    /// Connected to the named network.
    Connected(Ssid),
}
