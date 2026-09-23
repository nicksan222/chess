//! Run a Rust integration-test probe inside an isolated Linux installation.
//!
//! A fixture supplies the distribution, services and startup script. The
//! harness runs a dedicated Rust probe executable inside that installation.
//! Kernel-specific features (such as mac80211_hwsim) need a VM backend.

use std::{error::Error, path::Path};

use super::probe_case::ProbeCase;

use testcontainers::{
    GenericBuildableImage, GenericImage, ImageExt,
    core::{ContainerAsync, ExecCommand, WaitFor},
    runners::{AsyncBuilder, AsyncRunner},
};

/// An independently started Linux installation and its readiness signal.
pub struct LinuxFixture {
    pub image_name: &'static str,
    pub dockerfile: &'static str,
    pub startup_script: &'static [u8],
    pub ready_message: &'static str,
}

pub struct LinuxHarness {
    container: ContainerAsync<GenericImage>,
}

impl LinuxHarness {
    pub async fn start(fixture: LinuxFixture, probe_binary: &str) -> Result<Self, Box<dyn Error>> {
        let image = GenericBuildableImage::new(fixture.image_name, "local")
            .with_dockerfile_string(fixture.dockerfile)
            .with_data(fixture.startup_script.to_vec(), "./start.sh")
            .build_image()
            .await?;

        let container = image
            .with_wait_for(WaitFor::message_on_stdout(fixture.ready_message))
            .with_network("none")
            .with_copy_to("/firmware-probe", Path::new(probe_binary))
            .start()
            .await?;

        Ok(Self { container })
    }

    /// Run a named scenario inside Linux, failing with its captured output.
    pub async fn run_probe(&self, case: ProbeCase) -> Result<(), Box<dyn Error>> {
        let name = case.as_arg();
        let mut result = self
            .container
            .exec(ExecCommand::new(["/firmware-probe", name]))
            .await?;
        let stdout = String::from_utf8(result.stdout_to_vec().await?)?;
        let stderr = String::from_utf8(result.stderr_to_vec().await?)?;
        let exit_code = result.exit_code().await?;
        assert_eq!(exit_code, Some(0), "{stdout}\n{stderr}");
        assert!(
            stdout.contains(&format!("{name}: ok")),
            "probe did not complete: {stdout}\n{stderr}"
        );
        Ok(())
    }
}
