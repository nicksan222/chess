//! Boots a disposable Linux VM as a testcontainers-managed fixture.
//! Guest-specific kernel devices and setup live in the fixture files; tests
//! supply a Rust probe executable and wait for an explicit success marker.

use std::{error::Error, path::Path, time::Duration};

use testcontainers::{
    GenericBuildableImage, ImageExt,
    bollard::models::DeviceMapping,
    core::WaitFor,
    runners::{AsyncBuilder, AsyncRunner},
};

pub struct VmFixture {
    pub image_name: &'static str,
    pub dockerfile: &'static str,
    pub start_script: &'static [u8],
    pub bootstrap_script: &'static [u8],
    pub user_data: &'static [u8],
    pub meta_data: &'static [u8],
    pub success_message: &'static str,
}

impl VmFixture {
    pub async fn run(self, probe_binary: &Path) -> Result<(), Box<dyn Error>> {
        let image = GenericBuildableImage::new(self.image_name, "local")
            .with_dockerfile_string(self.dockerfile)
            .with_data(self.start_script.to_vec(), "./start.sh")
            .with_data(self.bootstrap_script.to_vec(), "./bootstrap.sh")
            .with_data(self.user_data.to_vec(), "./user-data")
            .with_data(self.meta_data.to_vec(), "./meta-data")
            .build_image()
            .await?;

        let container = image
            .with_wait_for(WaitFor::message_on_stdout(self.success_message))
            .with_startup_timeout(Duration::from_secs(900))
            .with_copy_to("/firmware-probe", probe_binary);
        let container = if Path::new("/dev/kvm").exists() {
            container.with_host_config_modifier(|config| {
                config.devices = Some(vec![DeviceMapping {
                    path_on_host: Some("/dev/kvm".into()),
                    path_in_container: Some("/dev/kvm".into()),
                    cgroup_permissions: Some("rwm".into()),
                }]);
            })
        } else {
            container
        };

        // The guest runs its own kernel; no host D-Bus or network devices are shared.
        let _vm = tokio::time::timeout(Duration::from_secs(900), container.start()).await??;
        Ok(())
    }
}
