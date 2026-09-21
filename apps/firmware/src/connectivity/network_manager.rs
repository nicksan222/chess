//! NetworkManager integration implemented with the typed `nmrs` D-Bus client.

use std::fmt;

use nmrs::{
    NetworkManager, WifiScope, WifiSecurity,
    builders::{WifiConnectionBuilder, WifiMode},
};
use tokio::sync::Mutex;

use super::{AccessPoint, Credentials, Hotspot, InvalidSsid, Security, Ssid, Status};

const WIFI_INTERFACE: &str = "wlan0";

/// Failure returned by connectivity operations.
#[derive(Debug)]
pub enum Error {
    /// The D-Bus client or NetworkManager rejected an operation.
    NetworkManager(Box<nmrs::ConnectionError>),
    /// NetworkManager returned an SSID outside the product model's constraints.
    InvalidSsid(InvalidSsid),
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NetworkManager(error) => write!(formatter, "NetworkManager failed: {error}"),
            Self::InvalidSsid(error) => error.fmt(formatter),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::NetworkManager(error) => Some(error),
            Self::InvalidSsid(error) => Some(error),
        }
    }
}

impl From<nmrs::ConnectionError> for Error {
    fn from(error: nmrs::ConnectionError) -> Self {
        Self::NetworkManager(Box::new(error))
    }
}

/// Product Wi-Fi operations backed by NetworkManager.
pub struct Connectivity {
    manager: NetworkManager,
    wifi: WifiScope,
    hotspot_ssid: Mutex<Option<String>>,
}

impl Connectivity {
    /// Connects to the system NetworkManager service and the board Wi-Fi radio.
    pub async fn network_manager() -> Result<Self, Error> {
        let manager = NetworkManager::new().await?;
        let wifi = manager.wifi(WIFI_INTERFACE);
        Ok(Self {
            manager,
            wifi,
            hotspot_ssid: Mutex::new(None),
        })
    }

    /// Reports the current client connection.
    pub async fn status(&self) -> Result<Status, Error> {
        self.manager
            .current_ssid()
            .await
            .map(Ssid::new)
            .transpose()
            .map(|ssid| ssid.map_or(Status::Disconnected, Status::Connected))
            .map_err(Error::InvalidSsid)
    }

    /// Refreshes and returns visible networks.
    pub async fn scan(&self) -> Result<Vec<AccessPoint>, Error> {
        self.wifi.scan().await?;
        let mut networks = self
            .wifi
            .list_networks()
            .await?
            .into_iter()
            .filter_map(|network| {
                let ssid = Ssid::new(network.ssid).ok()?;
                let security = if network.is_eap {
                    Security::Enterprise
                } else if network.secured {
                    Security::Personal
                } else {
                    Security::Open
                };
                Some(AccessPoint {
                    ssid,
                    signal: network.strength.unwrap_or(0),
                    security,
                    connected: network.is_active,
                    known: network.known,
                })
            })
            .collect::<Vec<_>>();
        networks.sort_by(|left, right| {
            right
                .signal
                .cmp(&left.signal)
                .then_with(|| left.ssid.cmp(&right.ssid))
        });
        Ok(networks)
    }

    /// Starts the provisioning hotspot.
    pub async fn start_hotspot(&self, hotspot: &Hotspot) -> Result<(), Error> {
        self.stop_hotspot().await?;
        self.wifi.forget(hotspot.ssid.as_str()).await?;
        let settings = WifiConnectionBuilder::new(hotspot.ssid.as_str())
            .wpa_psk(hotspot.passphrase.expose())
            .mode(WifiMode::Ap)
            .autoconnect(false)
            .ipv4_shared()
            .ipv6_ignore()
            .build();
        self.manager
            .add_and_activate_connection(settings, Some(WIFI_INTERFACE), None)
            .await?;
        *self.hotspot_ssid.lock().await = Some(hotspot.ssid.as_str().to_owned());
        Ok(())
    }

    /// Stops and removes the provisioning hotspot.
    pub async fn stop_hotspot(&self) -> Result<(), Error> {
        if let Some(ssid) = self.hotspot_ssid.lock().await.take() {
            self.wifi.forget(&ssid).await?;
        }
        Ok(())
    }

    /// Stops hotspot mode and joins the selected client network.
    pub async fn connect(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error> {
        self.stop_hotspot().await?;
        let security = match credentials {
            Credentials::Open => WifiSecurity::Open,
            Credentials::Personal(passphrase) => WifiSecurity::WpaPsk {
                psk: passphrase.expose().to_owned(),
            },
        };
        self.wifi.connect(ssid.as_str(), security).await?;
        Ok(())
    }
}
