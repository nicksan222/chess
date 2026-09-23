//! The production Wi-Fi API talks to guest-kernel radios and real Linux services.

use std::path::Path;

use super::vm::VmFixture;

#[tokio::test]
async fn firmware_joins_open_and_wpa_networks_and_starts_a_hotspot_in_linux_vm()
-> Result<(), Box<dyn std::error::Error>> {
    VmFixture {
        image_name: "firmware-wifi-vm",
        dockerfile: include_str!("wifi-vm/Dockerfile"),
        start_script: include_bytes!("wifi-vm/start.sh"),
        bootstrap_script: include_bytes!("wifi-vm/bootstrap.sh"),
        user_data: include_bytes!("wifi-vm/user-data"),
        meta_data: include_bytes!("wifi-vm/meta-data"),
        success_message: "WIFI_VM_PASS",
    }
    .run(Path::new(env!("CARGO_BIN_EXE_firmware-linux-probe")))
    .await
}
