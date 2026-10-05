//! The NetworkManager implementation of [`WifiBackend`], using the typed `nmrs` D-Bus client.
//! This is the only module that calls `nmrs`.

use nmrs::{
    NetworkManager, WifiScope, WifiSecurity,
    builders::{WifiConnectionBuilder, WifiMode},
};

use super::{
    Credentials, Error, Hotspot, Ssid,
    backend::{VisibleNetwork, WifiBackend},
};

const WIFI_INTERFACE: &str = "wlan0";

/// Wi-Fi control through the system NetworkManager service.
pub struct NetworkManagerBackend {
    manager: NetworkManager,
    wifi: WifiScope,
}

impl NetworkManagerBackend {
    /// Connects to the system NetworkManager service and the board Wi-Fi radio.
    pub async fn connect() -> Result<Self, Error> {
        let manager = NetworkManager::new().await?;
        let wifi = manager.wifi(WIFI_INTERFACE);
        Ok(Self { manager, wifi })
    }
}

impl WifiBackend for NetworkManagerBackend {
    async fn current_ssid(&self) -> Option<String> {
        self.manager.current_ssid().await
    }

    async fn scan(&self) -> Result<Vec<VisibleNetwork>, Error> {
        self.wifi.scan().await?;
        Ok(self
            .wifi
            .list_networks()
            .await?
            .into_iter()
            .map(|network| VisibleNetwork {
                ssid: network.ssid,
                strength: network.strength,
                secured: network.secured,
                enterprise: network.is_eap,
                active: network.is_active,
                known: network.known,
            })
            .collect())
    }

    async fn forget(&self, ssid: &str) -> Result<(), Error> {
        Ok(self.wifi.forget(ssid).await?)
    }

    async fn start_access_point(&self, hotspot: &Hotspot) -> Result<(), Error> {
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
        Ok(())
    }

    async fn join(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error> {
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
