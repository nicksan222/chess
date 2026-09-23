//! Executed inside the testcontainers Linux fixture, never on the host bus.

use std::{
    error::Error as StdError,
    fs,
    process::{Child, Command, Stdio},
    time::Duration,
};

use firmware::connectivity::{
    Connectivity, Credentials, Error, Hotspot, Passphrase, Security, Ssid, Status,
};

mod probe_case;
use probe_case::ProbeCase;

fn main() -> Result<(), Box<dyn StdError>> {
    let case = match std::env::args().nth(1) {
        Some(name) => ProbeCase::from_arg(&name).ok_or("unknown probe name")?,
        None => ProbeCase::WifiJourney, // The VM runs this binary without arguments.
    };
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?;

    runtime.block_on(async {
        match case {
            ProbeCase::DisconnectedAndScan => disconnected_and_scan().await,
            ProbeCase::OpenNetworkWithoutRadio => open_network().await,
            ProbeCase::PersonalNetworkWithoutRadio => personal_network().await,
            ProbeCase::HotspotWithoutRadio => hotspot().await,
            ProbeCase::WifiJourney => wifi_journey().await,
        }
    });
    println!("{}: ok", case.as_arg());
    Ok(())
}

const OPEN_SSID: &str = "ChessOpen";
const WPA_SSID: &str = "ChessWpa";
const WPA_PASSWORD: &str = "correct-password";

struct Hostapd(Child);

impl Hostapd {
    fn start(ssid: &str, wpa_password: Option<&str>) -> Self {
        let security = match wpa_password {
            Some(password) => format!(
                "wpa=2\nwpa_key_mgmt=WPA-PSK\nrsn_pairwise=CCMP\nwpa_passphrase={password}\n"
            ),
            None => String::new(),
        };
        let config = format!(
            "interface=wlan1\ndriver=nl80211\nssid={ssid}\nhw_mode=g\nchannel=1\nauth_algs=1\n{security}"
        );
        let path = "/tmp/firmware-hostapd.conf";
        fs::write(path, config).unwrap();
        let child = Command::new("hostapd")
            .arg(path)
            .stdout(Stdio::null())
            .spawn()
            .expect("start a real access point on the second guest radio");
        Self(child)
    }
}

impl Drop for Hostapd {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

async fn visible_network(connectivity: &Connectivity, ssid: &Ssid, security: Security) {
    for _ in 0..20 {
        if let Ok(networks) = connectivity.scan().await
            && networks
                .iter()
                .any(|network| network.ssid == *ssid && network.security == security)
        {
            return;
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
    panic!("{ssid:?} with {security:?} was not visible on wlan0");
}

async fn wifi_journey() {
    let connectivity = Connectivity::network_manager().await.unwrap();
    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);

    let open_ap = Hostapd::start(OPEN_SSID, None);
    let open_ssid = Ssid::new(OPEN_SSID).unwrap();
    visible_network(&connectivity, &open_ssid, Security::Open).await;
    connectivity
        .connect(&open_ssid, &Credentials::Open)
        .await
        .unwrap();
    assert_eq!(
        connectivity.status().await.unwrap(),
        Status::Connected(open_ssid)
    );
    println!("open Wi-Fi association passed");
    drop(open_ap);

    let wpa_ap = Hostapd::start(WPA_SSID, Some(WPA_PASSWORD));
    let wpa_ssid = Ssid::new(WPA_SSID).unwrap();
    visible_network(&connectivity, &wpa_ssid, Security::Personal).await;
    let credentials = Credentials::Personal(Passphrase::new(WPA_PASSWORD).unwrap());
    connectivity.connect(&wpa_ssid, &credentials).await.unwrap();
    assert_eq!(
        connectivity.status().await.unwrap(),
        Status::Connected(wpa_ssid)
    );
    println!("WPA Wi-Fi association passed");
    drop(wpa_ap);

    let hotspot = Hotspot {
        ssid: Ssid::new("ChessSetup").unwrap(),
        passphrase: Passphrase::new("setup-password").unwrap(),
    };
    connectivity.start_hotspot(&hotspot).await.unwrap();
    let mut advertised = false;
    for _ in 0..20 {
        let scan = Command::new("iw")
            .args(["dev", "wlan1", "scan"])
            .output()
            .unwrap();
        if scan.status.success()
            && String::from_utf8_lossy(&scan.stdout).contains(hotspot.ssid.as_str())
        {
            advertised = true;
            break;
        }
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
    assert!(
        advertised,
        "the provisioning hotspot must be visible on wlan1"
    );
    connectivity.stop_hotspot().await.unwrap();
    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);
    println!("provisioning hotspot lifecycle passed");
}

async fn disconnected_and_scan() {
    let connectivity = Connectivity::network_manager().await.unwrap();

    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);
    let scan_error = connectivity.scan().await.expect_err("wlan0 is absent");
    assert!(
        matches!(scan_error, Error::NetworkManager(_)),
        "{scan_error:?}"
    );
}

async fn open_network() {
    let connectivity = Connectivity::network_manager().await.unwrap();
    let ssid = Ssid::new("Absent Open Network").unwrap();

    let error = connectivity
        .connect(&ssid, &Credentials::Open)
        .await
        .expect_err("joining an open network without wlan0 must fail");
    assert!(matches!(error, Error::NetworkManager(_)), "{error:?}");
    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);
}

async fn personal_network() {
    let connectivity = Connectivity::network_manager().await.unwrap();
    let ssid = Ssid::new("Absent WPA Network").unwrap();
    let credentials = Credentials::Personal(Passphrase::new("test-password").unwrap());

    let error = connectivity
        .connect(&ssid, &credentials)
        .await
        .expect_err("joining a WPA network without wlan0 must fail");
    assert!(matches!(error, Error::NetworkManager(_)), "{error:?}");
    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);
}

async fn hotspot() {
    let connectivity = Connectivity::network_manager().await.unwrap();
    let hotspot = Hotspot {
        ssid: Ssid::new("Chess Setup").unwrap(),
        passphrase: Passphrase::new("setup-password").unwrap(),
    };

    connectivity.stop_hotspot().await.unwrap(); // Nothing to stop.
    connectivity.stop_hotspot().await.unwrap(); // Repeated stop is safe.
    let error = connectivity
        .start_hotspot(&hotspot)
        .await
        .expect_err("an AP cannot start without wlan0");
    assert!(matches!(error, Error::NetworkManager(_)), "{error:?}");
    connectivity.stop_hotspot().await.unwrap(); // Failed start leaves no active hotspot.
    assert_eq!(connectivity.status().await.unwrap(), Status::Disconnected);
}
