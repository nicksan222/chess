//! The firmware this process is: its name and version, as built.

use semver::Version;

/// The product name in `--version`, logs and network user agents.
pub const NAME: &str = "firmware";

/// The version of the running firmware, from its Cargo package.
///
/// Release tags name this version as `v<version>`, so a newer published tag
/// means newer firmware.
pub fn version() -> Version {
    Version::parse(env!("CARGO_PKG_VERSION")).expect("Cargo package versions are semantic")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_package_version_is_the_installed_version() {
        assert_eq!(version().to_string(), env!("CARGO_PKG_VERSION"));
    }
}
