//! Product Wi-Fi operations, independent of how the operating system provides them.

use tokio::sync::Mutex;

use super::{
    AccessPoint, Credentials, Error, Hotspot, Security, Ssid, Status,
    backend::{VisibleNetwork, WifiBackend},
    network_manager::NetworkManagerBackend,
};

/// Product Wi-Fi operations.
///
/// The type parameter is the system backend. Callers use the default,
/// NetworkManager, through [`Connectivity::network_manager`]; unit tests supply
/// an in-memory backend with `Connectivity::with_backend`.
pub struct Connectivity<B = NetworkManagerBackend> {
    backend: B,
    hotspot_ssid: Mutex<Option<String>>,
}

impl Connectivity {
    /// Connects to the system NetworkManager service and the board Wi-Fi radio.
    pub async fn network_manager() -> Result<Self, Error> {
        Ok(Self::with_backend(NetworkManagerBackend::connect().await?))
    }
}

impl<B: WifiBackend> Connectivity<B> {
    pub(crate) fn with_backend(backend: B) -> Self {
        Self {
            backend,
            hotspot_ssid: Mutex::new(None),
        }
    }

    /// Reports the current client connection.
    pub async fn status(&self) -> Result<Status, Error> {
        self.backend
            .current_ssid()
            .await
            .map(Ssid::new)
            .transpose()
            .map(|ssid| ssid.map_or(Status::Disconnected, Status::Connected))
            .map_err(Error::InvalidSsid)
    }

    /// Refreshes and returns visible networks.
    pub async fn scan(&self) -> Result<Vec<AccessPoint>, Error> {
        let mut networks = self
            .backend
            .scan()
            .await?
            .into_iter()
            .filter_map(access_point)
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
        self.backend.forget(hotspot.ssid.as_str()).await?;
        self.backend.start_access_point(hotspot).await?;
        *self.hotspot_ssid.lock().await = Some(hotspot.ssid.as_str().to_owned());
        Ok(())
    }

    /// Stops and removes the provisioning hotspot.
    pub async fn stop_hotspot(&self) -> Result<(), Error> {
        if let Some(ssid) = self.hotspot_ssid.lock().await.take() {
            self.backend.forget(&ssid).await?;
        }
        Ok(())
    }

    /// Stops hotspot mode and joins the selected client network.
    pub async fn connect(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error> {
        self.stop_hotspot().await?;
        self.backend.join(ssid, credentials).await
    }
}

/// Validates a reported network and classifies its security; networks whose
/// names the product model rejects are omitted.
fn access_point(network: VisibleNetwork) -> Option<AccessPoint> {
    let ssid = Ssid::new(network.ssid).ok()?;
    let security = if network.enterprise {
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
        connected: network.active,
        known: network.known,
    })
}

#[cfg(test)]
mod tests {
    use nmrs::ConnectionError;

    use super::*;
    use crate::connectivity::{
        Passphrase,
        fake::{Call, Failure, FakeWifi, Network, Operation},
    };

    fn ssid(name: &str) -> Ssid {
        Ssid::new(name).unwrap()
    }

    fn personal(passphrase: &str) -> Credentials {
        Credentials::Personal(Passphrase::new(passphrase).unwrap())
    }

    fn hotspot(name: &str) -> Hotspot {
        Hotspot {
            ssid: ssid(name),
            passphrase: Passphrase::new("setup-password").unwrap(),
        }
    }

    fn connectivity(fake: &FakeWifi) -> Connectivity<FakeWifi> {
        Connectivity::with_backend(fake.clone())
    }

    fn names(networks: &[AccessPoint]) -> Vec<&str> {
        networks
            .iter()
            .map(|network| network.ssid.as_str())
            .collect()
    }

    // --- status ---

    #[tokio::test]
    async fn status_is_disconnected_when_no_network_is_active() {
        let wifi = connectivity(&FakeWifi::default());

        assert_eq!(wifi.status().await.unwrap(), Status::Disconnected);
    }

    #[tokio::test]
    async fn status_names_the_connected_network() {
        let wifi = connectivity(&FakeWifi::default().with_active_client("Home"));

        assert_eq!(
            wifi.status().await.unwrap(),
            Status::Connected(ssid("Home"))
        );
    }

    #[tokio::test]
    async fn status_rejects_an_active_network_name_the_product_cannot_represent() {
        for invalid in ["", "a\0b", &"x".repeat(33)] {
            let wifi = connectivity(&FakeWifi::default().with_active_client(invalid));

            let error = wifi.status().await.unwrap_err();

            assert!(
                matches!(error, Error::InvalidSsid(_)),
                "{invalid:?}: {error:?}"
            );
        }
    }

    // --- scan ---

    #[tokio::test]
    async fn scan_classifies_open_personal_and_enterprise_networks() {
        let fake = FakeWifi::default()
            .with_network(Network::open("Cafe", 50))
            .with_network(Network::wpa("Home", 50, "home-password"))
            .with_network(Network::enterprise("Campus", 50));

        let networks = connectivity(&fake).scan().await.unwrap();

        let security = |name: &str| {
            networks
                .iter()
                .find(|network| network.ssid.as_str() == name)
                .map(|network| network.security)
        };
        assert_eq!(security("Cafe"), Some(Security::Open));
        assert_eq!(security("Home"), Some(Security::Personal));
        // Enterprise networks are also "secured"; they must not be offered as Personal.
        assert_eq!(security("Campus"), Some(Security::Enterprise));
    }

    #[tokio::test]
    async fn scan_reports_an_unknown_signal_strength_as_zero() {
        let fake = FakeWifi::default().with_network(Network::open("Cafe", 80).without_strength());

        let networks = connectivity(&fake).scan().await.unwrap();

        assert_eq!(networks[0].signal, 0);
    }

    #[tokio::test]
    async fn scan_lists_the_strongest_first_and_breaks_ties_by_name() {
        let fake = FakeWifi::default()
            .with_network(Network::open("weak", 10))
            .with_network(Network::open("b", 70))
            .with_network(Network::open("strong", 90))
            .with_network(Network::open("a", 70))
            .with_network(Network::open("unreported", 0).without_strength());

        let networks = connectivity(&fake).scan().await.unwrap();

        assert_eq!(names(&networks), ["strong", "a", "b", "weak", "unreported"]);
    }

    #[tokio::test]
    async fn scan_omits_networks_whose_names_the_product_cannot_represent() {
        let fake = FakeWifi::default()
            .with_network(Network::open("", 90)) // Empty name.
            .with_network(Network::open(&"x".repeat(33), 80)) // Over 32 bytes.
            .with_network(Network::open("nul\0inside", 70))
            .with_network(Network::open(&"y".repeat(32), 60)) // Exactly 32 bytes is fine.
            .with_network(Network::open("Cafe", 50));

        let networks = connectivity(&fake).scan().await.unwrap();

        assert_eq!(names(&networks), ["y".repeat(32).as_str(), "Cafe"]);
    }

    #[tokio::test]
    async fn scan_reports_which_network_is_connected_and_which_are_saved() {
        let fake = FakeWifi::default()
            .with_network(Network::open("Cafe", 60))
            .with_network(Network::wpa("Home", 50, "home-password"))
            .with_network(Network::open("Other", 40));
        let wifi = connectivity(&fake);
        let before = wifi.scan().await.unwrap();
        assert!(
            before
                .iter()
                .all(|network| !network.connected && !network.known)
        );

        wifi.connect(&ssid("Home"), &personal("home-password"))
            .await
            .unwrap();
        wifi.connect(&ssid("Cafe"), &Credentials::Open)
            .await
            .unwrap();
        let after = wifi.scan().await.unwrap();

        let flags: Vec<_> = after
            .iter()
            .map(|network| (network.ssid.as_str(), network.connected, network.known))
            .collect();
        // Home was joined earlier and is saved but no longer active.
        assert_eq!(
            flags,
            [
                ("Cafe", true, true),
                ("Home", false, true),
                ("Other", false, false)
            ]
        );
    }

    #[tokio::test]
    async fn scan_propagates_a_backend_failure() {
        let fake = FakeWifi::default();
        fake.fail_next(Operation::Scan, Failure::Timeout);

        let error = connectivity(&fake).scan().await.unwrap_err();

        assert!(
            matches!(&error, Error::NetworkManager(inner)
            if matches!(**inner, ConnectionError::Timeout)),
            "{error:?}"
        );
    }

    // --- hotspot ---

    #[tokio::test]
    async fn starting_the_hotspot_stops_the_previous_one_then_forgets_the_new_name_then_starts() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);

        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        assert_eq!(
            fake.calls(),
            [
                Call::Forget("Setup".into()),
                Call::StartAccessPoint(hotspot("Setup"))
            ]
        );

        fake.clear_calls();
        wifi.start_hotspot(&hotspot("Setup2")).await.unwrap();
        assert_eq!(
            fake.calls(),
            [
                Call::Forget("Setup".into()), // The remembered hotspot is stopped first.
                Call::Forget("Setup2".into()),
                Call::StartAccessPoint(hotspot("Setup2")),
            ]
        );
    }

    #[tokio::test]
    async fn restarting_the_same_hotspot_leaves_a_single_access_point_and_profile() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);

        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();

        assert_eq!(fake.access_point().as_deref(), Some("Setup"));
        assert_eq!(fake.profiles(), ["Setup"]);
    }

    #[tokio::test]
    async fn replacing_the_hotspot_leaves_only_the_new_access_point_and_profile() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);

        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        wifi.start_hotspot(&hotspot("Setup2")).await.unwrap();

        assert_eq!(fake.access_point().as_deref(), Some("Setup2"));
        assert_eq!(fake.profiles(), ["Setup2"]);
    }

    #[tokio::test]
    async fn stopping_the_hotspot_forgets_exactly_the_one_that_was_started() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);
        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        fake.clear_calls();

        wifi.stop_hotspot().await.unwrap();

        assert_eq!(fake.calls(), [Call::Forget("Setup".into())]);
        assert_eq!(fake.access_point(), None);
        assert!(fake.profiles().is_empty());
    }

    #[tokio::test]
    async fn stopping_without_a_running_hotspot_makes_no_backend_calls() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);

        wifi.stop_hotspot().await.unwrap(); // Never started.
        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        wifi.stop_hotspot().await.unwrap();
        fake.clear_calls();
        wifi.stop_hotspot().await.unwrap(); // Already stopped.

        assert_eq!(fake.calls(), []);
    }

    #[tokio::test]
    async fn a_hotspot_that_failed_to_start_is_not_remembered() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);
        fake.fail_next(Operation::StartAccessPoint, Failure::Timeout);

        let error = wifi.start_hotspot(&hotspot("Setup")).await.unwrap_err();
        assert!(matches!(error, Error::NetworkManager(_)), "{error:?}");
        fake.clear_calls();
        wifi.stop_hotspot().await.unwrap();

        assert_eq!(
            fake.calls(),
            [],
            "nothing was started, so nothing is stopped"
        );
        assert_eq!(fake.access_point(), None);
    }

    #[tokio::test]
    async fn a_forget_failure_stops_the_hotspot_start_and_is_reported() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);
        fake.fail_next(Operation::Forget, Failure::Timeout);

        let error = wifi.start_hotspot(&hotspot("Setup")).await.unwrap_err();

        assert!(
            matches!(&error, Error::NetworkManager(inner)
            if matches!(**inner, ConnectionError::Timeout)),
            "{error:?}"
        );
        assert_eq!(
            fake.calls(),
            [Call::Forget("Setup".into())],
            "no access point is started after a failed forget"
        );
        assert_eq!(fake.access_point(), None);
    }

    // --- connect ---

    #[tokio::test]
    async fn connecting_stops_a_running_hotspot_before_joining() {
        let fake = FakeWifi::default().with_network(Network::open("Cafe", 60));
        let wifi = connectivity(&fake);
        wifi.start_hotspot(&hotspot("Setup")).await.unwrap();
        fake.clear_calls();

        wifi.connect(&ssid("Cafe"), &Credentials::Open)
            .await
            .unwrap();

        assert_eq!(
            fake.calls(),
            [
                Call::Forget("Setup".into()),
                Call::Join(ssid("Cafe"), Credentials::Open)
            ]
        );
        assert_eq!(fake.access_point(), None);
        assert_eq!(
            wifi.status().await.unwrap(),
            Status::Connected(ssid("Cafe"))
        );
    }

    #[tokio::test]
    async fn connecting_without_a_hotspot_only_joins() {
        let fake = FakeWifi::default().with_network(Network::open("Cafe", 60));

        connectivity(&fake)
            .connect(&ssid("Cafe"), &Credentials::Open)
            .await
            .unwrap();

        assert_eq!(fake.calls(), [Call::Join(ssid("Cafe"), Credentials::Open)]);
    }

    #[tokio::test]
    async fn open_and_wpa_credentials_reach_the_backend_unchanged() {
        let fake = FakeWifi::default()
            .with_network(Network::open("Cafe", 60))
            .with_network(Network::wpa("Home", 50, "home-password"));
        let wifi = connectivity(&fake);

        wifi.connect(&ssid("Cafe"), &Credentials::Open)
            .await
            .unwrap();
        wifi.connect(&ssid("Home"), &personal("home-password"))
            .await
            .unwrap();

        assert_eq!(
            fake.calls(),
            [
                Call::Join(ssid("Cafe"), Credentials::Open),
                Call::Join(ssid("Home"), personal("home-password")),
            ]
        );
        assert_eq!(
            wifi.status().await.unwrap(),
            Status::Connected(ssid("Home"))
        );
    }

    #[tokio::test]
    async fn a_wrong_passphrase_is_reported_and_leaves_the_board_disconnected() {
        let fake = FakeWifi::default().with_network(Network::wpa("Home", 50, "home-password"));
        let wifi = connectivity(&fake);

        let error = wifi
            .connect(&ssid("Home"), &personal("not-the-password"))
            .await
            .unwrap_err();

        assert!(
            matches!(&error, Error::NetworkManager(inner)
            if matches!(**inner, ConnectionError::AuthFailed)),
            "{error:?}"
        );
        // The fake, like NetworkManager in the earlier VM runs, keeps no link after a failed join.
        assert_eq!(wifi.status().await.unwrap(), Status::Disconnected);
    }

    #[tokio::test]
    async fn a_network_that_is_not_in_range_is_reported_and_leaves_the_board_disconnected() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);

        let error = wifi
            .connect(&ssid("Nowhere"), &Credentials::Open)
            .await
            .unwrap_err();

        assert!(
            matches!(&error, Error::NetworkManager(inner)
            if matches!(**inner, ConnectionError::NotFound)),
            "{error:?}"
        );
        // The fake, like NetworkManager in the earlier VM runs, keeps no link after a failed join.
        assert_eq!(wifi.status().await.unwrap(), Status::Disconnected);
    }

    // --- known bugs: these assert the documented behaviour and fail today ---

    /// Evidence: the removed Linux VM run reported
    /// `status with only the hotspot running: Connected(Ssid("ChessSetup"))`.
    /// `Status` is documented as the current *client* connection.
    #[tokio::test]
    #[ignore = "bug (Q1): status() reports Connected(<hotspot SSID>) while only the hotspot runs"]
    async fn a_running_hotspot_is_not_a_client_connection() {
        let fake = FakeWifi::default();
        let wifi = connectivity(&fake);
        wifi.start_hotspot(&hotspot("ChessSetup")).await.unwrap();

        assert_eq!(wifi.status().await.unwrap(), Status::Disconnected);
    }

    /// Evidence: in the removed VM run, after the first `Connectivity` was dropped a new
    /// one's `stop_hotspot()` left `wlan0` as `type AP ssid ChessSetup` with the profile
    /// still saved, because the SSID is remembered only in memory.
    #[tokio::test]
    #[ignore = "bug (Q5): hotspot survives a firmware restart; a new Connectivity cannot stop it"]
    async fn a_restarted_firmware_can_stop_the_hotspot_it_left_running() {
        let fake = FakeWifi::default();
        let before_restart = connectivity(&fake);
        before_restart
            .start_hotspot(&hotspot("ChessSetup"))
            .await
            .unwrap();
        drop(before_restart);

        let after_restart = connectivity(&fake);
        after_restart.stop_hotspot().await.unwrap();

        assert_eq!(fake.access_point(), None);
    }
}
