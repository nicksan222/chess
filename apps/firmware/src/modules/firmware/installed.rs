//! The firmware this process is: its name and version, as built.

use semver::Version;

/// The product name in `--version`, logs and network user agents.
pub const NAME: &str = "firmware";

/// The version of the running firmware, from its Cargo package.
///
/// Release tags name this version as `v<version>`, so a newer published tag
/// means newer firmware.
///
/// # Panics
///
/// Never in a built package: Cargo rejects a non-semantic package version.
#[expect(
    clippy::expect_used,
    reason = "Cargo itself rejects a package version that is not semantic"
)]
pub fn version() -> Version {
    Version::parse(env!("CARGO_PKG_VERSION")).expect("Cargo package versions are semantic")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_name_is_the_package_name() {
        assert_eq!(NAME, env!("CARGO_PKG_NAME"));
    }

    #[test]
    fn the_package_version_is_the_installed_version() {
        assert_eq!(version().to_string(), env!("CARGO_PKG_VERSION"));
    }
}
