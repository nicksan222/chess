//! The `NetworkManager` implementation of [`WifiBackend`], using the typed `nmrs` D-Bus client.
//! This is the only module that calls `nmrs`.

use crate::board::WIFI_INTERFACE;
use nmrs::{
    DeviceState, NetworkManager, WifiScope, WifiSecurity,
    builders::{WifiConnectionBuilder, WifiMode},
};

use super::{
    Credentials, Error, Hotspot, Ssid,
    backend::{Radio, VisibleNetwork, WifiBackend},
};

/// Wi-Fi control through the system `NetworkManager` service.
pub(super) struct NetworkManagerBackend {
    manager: NetworkManager,
    wifi: WifiScope,
}

impl NetworkManagerBackend {
    /// Connects to the system `NetworkManager` service and the board Wi-Fi radio.
    pub(super) async fn connect() -> Result<Self, Error> {
        let manager = NetworkManager::new().await?;
        let wifi = manager.wifi(WIFI_INTERFACE);
        Ok(Self { manager, wifi })
    }
}

impl WifiBackend for NetworkManagerBackend {
    async fn radio(&self) -> Result<Radio, Error> {
        // `current_ssid` turns every D-Bus failure into "no network", so the
        // device state is read instead, keeping failures as errors.
        let device = self
            .manager
            .wifi_device_by_interface(WIFI_INTERFACE)
            .await?;
        Ok(match device.state {
            // `Unavailable` is a managed radio that is switched off.
            DeviceState::Disconnected | DeviceState::Unavailable => Radio::Disconnected,
            DeviceState::Activated => Radio::Active {
                ssid: device.active_ssid,
            },
            DeviceState::Prepare
            | DeviceState::Config
            | DeviceState::NeedAuth
            | DeviceState::IpConfig
            | DeviceState::IpCheck
            | DeviceState::Secondaries
            | DeviceState::Deactivating => Radio::Changing,
            // Unmanaged, failed, and states added after this was written.
            _ => Radio::Unknown,
        })
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
