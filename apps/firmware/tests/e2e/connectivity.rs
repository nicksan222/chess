//! Black-box checks against real NetworkManager and system D-Bus in Linux.

use firmware::connectivity::{Passphrase, Ssid};

use super::{
    linux::{LinuxFixture, LinuxHarness},
    probe_case::ProbeCase,
};

#[tokio::test]
async fn connectivity_uses_real_linux_network_manager() -> Result<(), Box<dyn std::error::Error>> {
    let linux = LinuxHarness::start(
        LinuxFixture {
            image_name: "firmware-network-manager",
            dockerfile: include_str!("linux-fixture/Dockerfile"),
            startup_script: include_bytes!("linux-fixture/start.sh"),
            ready_message: "NetworkManager ready",
        },
        env!("CARGO_BIN_EXE_firmware-linux-probe"),
    )
    .await?;

    linux.run_probe(ProbeCase::DisconnectedAndScan).await?;
    linux.run_probe(ProbeCase::OpenNetworkWithoutRadio).await?;
    linux
        .run_probe(ProbeCase::PersonalNetworkWithoutRadio)
        .await?;
    linux.run_probe(ProbeCase::HotspotWithoutRadio).await?;
    Ok(())
}

#[test]
fn ssid_validation_uses_bytes_and_rejects_empty_or_nul() {
    assert!(Ssid::new("").is_err());
    assert!(Ssid::new("a\0b").is_err());
    assert!(Ssid::new("é".repeat(17)).is_err()); // 34 bytes, not 17.
    assert!(Ssid::new("é".repeat(16)).is_ok()); // Exactly 32 bytes.
    assert!(Ssid::new("a".repeat(32)).is_ok());
}

#[test]
fn passphrase_validation_and_debug_redaction() {
    assert!(Passphrase::new("short").is_err());
    assert!(Passphrase::new("abcdefgh\n").is_err()); // Control character.
    assert!(Passphrase::new("a".repeat(65)).is_err());
    assert!(Passphrase::new("g".repeat(64)).is_err()); // Not hexadecimal.

    for valid in ["12345678".to_owned(), "a".repeat(63), "f".repeat(64)] {
        let passphrase = Passphrase::new(valid.clone()).unwrap();
        assert!(!format!("{passphrase:?}").contains(&valid));
    }
}
