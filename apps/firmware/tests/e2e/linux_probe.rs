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
use firmware::{
    hardware::{
        HardwareEvent,
        linux_gpio::LinuxGpioReader,
        pins::{BoardPins, ButtonEvent, Level, ReadLevel},
    },
    runtime::Firmware,
};
use probe_case::ProbeCase;

fn main() -> Result<(), Box<dyn StdError>> {
    let case = match std::env::args().nth(1) {
        Some(name) => ProbeCase::from_arg(&name).ok_or("unknown probe name")?,
        None => ProbeCase::LinuxJourney, // The VM runs this binary without arguments.
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
            ProbeCase::LinuxJourney => {
                wifi_journey().await;
                gpio_journey().await;
            }
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

async fn gpio_journey() {
    // The existing scripted tests cover every mapping and debounce edge case.
    // One real chardev transition proves the Linux reader -> runtime boundary.
    let config = std::path::Path::new("/sys/kernel/config/gpio-sim/chess-panel");
    let platform = fs::read_to_string(config.join("dev_name")).unwrap();
    let chip = fs::read_to_string(config.join("board/chip_name")).unwrap();
    let chip = chip.trim();
    let device = std::path::Path::new("/dev").join(chip);
    let pin = BoardPins::get().gpio.down_button;
    let pull = std::path::Path::new("/sys/devices/platform")
        .join(platform.trim())
        .join(chip)
        .join(format!("sim_gpio{}/pull", pin.bcm_number()));
    assert!(device.exists(), "missing GPIO character device: {device:?}");
    fs::write(&pull, "pull-up").unwrap();
    let mut reader = LinuxGpioReader::with_external_bias(&device);
    assert_eq!(reader.read_level(pin.gpio()).unwrap(), Level::High);
    let mut firmware = Firmware::start().unwrap();
    let _subscription = pin.start_subscription(reader, &firmware.events()).unwrap();
    tokio::time::sleep(Duration::from_millis(50)).await;
    assert_eq!(firmware.snapshot().processed_events, 0);

    fs::write(&pull, "pull-down").unwrap();
    let pressed = tokio::time::timeout(Duration::from_secs(5), firmware.after(0))
        .await
        .expect("Linux GPIO press should reach the firmware runtime")
        .unwrap();
    assert_eq!(pressed.processed_events, 1);
    assert_eq!(
        pressed.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Pressed(pin.button())))
    );

    fs::write(&pull, "pull-up").unwrap();
    let released = tokio::time::timeout(Duration::from_secs(5), firmware.after(1))
        .await
        .expect("Linux GPIO release should reach the firmware runtime")
        .unwrap();
    assert_eq!(released.processed_events, 2);
    assert_eq!(
        released.last_event,
        Some(HardwareEvent::Button(ButtonEvent::Released(pin.button())))
    );
    firmware.shutdown().await.unwrap();
    println!("Linux GPIO character-device button transition passed");
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
