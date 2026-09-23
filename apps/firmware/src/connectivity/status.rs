use super::Ssid;

/// Current client connection state.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Status {
    /// No active Wi-Fi client connection.
    Disconnected,
    /// Connected to the named network.
    Connected(Ssid),
}
