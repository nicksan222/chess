//! Published releases and how they compare with the installed firmware.

use std::cmp::Ordering;

use semver::Version;

use super::Error;

/// A published firmware release.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Release {
    pub version: Version,
    /// Human-readable release page.
    pub page: String,
}

/// Whether newer firmware than the installed one is published.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Availability {
    /// Nothing is published yet.
    NoRelease,
    /// The latest release is not newer than the installed firmware.
    UpToDate,
    /// A newer release.
    Available(Release),
}

impl Availability {
    /// Compares the latest release, tagged `v<version>`, with `installed`.
    /// Build metadata never makes a release newer.
    pub(super) fn of(tag: &str, page: &str, installed: &Version) -> Result<Self, Error> {
        let version = tag
            .strip_prefix('v')
            .and_then(|version| Version::parse(version).ok())
            .ok_or_else(|| Error::InvalidTag(tag.to_owned()))?;
        Ok(match version.cmp_precedence(installed) {
            Ordering::Greater => Self::Available(Release {
                version,
                page: page.to_owned(),
            }),
            Ordering::Less | Ordering::Equal => Self::UpToDate,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn only_a_higher_precedence_tag_is_available() {
        let installed = Version::new(1, 2, 0);
        assert_eq!(
            Availability::of("v1.3.0", "page", &installed),
            Ok(Availability::Available(Release {
                version: Version::new(1, 3, 0),
                page: "page".into(),
            }))
        );
        for tag in ["v1.2.0", "v1.1.9", "v1.2.0+build.7", "v1.2.0-rc.1"] {
            assert_eq!(
                Availability::of(tag, "page", &installed),
                Ok(Availability::UpToDate),
                "{tag}"
            );
        }
        let rc = Version::parse("1.2.0-rc.1").unwrap();
        assert!(matches!(
            Availability::of("v1.2.0", "page", &rc),
            Ok(Availability::Available(_))
        ));
    }

    #[test]
    fn a_prerelease_above_the_installed_version_is_newer() {
        let installed = Version::new(1, 2, 0);
        assert!(matches!(
            Availability::of("v1.3.0-rc.1", "page", &installed),
            Ok(Availability::Available(Release { version, .. })) if version.pre.as_str() == "rc.1"
        ));
    }

    #[test]
    fn build_metadata_never_decides() {
        let installed = Version::parse("1.2.0+device.4").unwrap();
        assert_eq!(
            Availability::of("v1.2.0+ci.9", "page", &installed),
            Ok(Availability::UpToDate)
        );
    }

    #[test]
    fn rejects_tags_that_are_not_v_semver() {
        for tag in [
            "1.3.0", "v1.3", "latest", "V1.3.0", " v1.3.0", "v1.3.0 ", "",
        ] {
            assert_eq!(
                Availability::of(tag, "page", &Version::new(1, 0, 0)),
                Err(Error::InvalidTag(tag.into()))
            );
        }
    }
}
