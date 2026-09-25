//! Black-box checks against real NetworkManager and system D-Bus in Linux.

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
