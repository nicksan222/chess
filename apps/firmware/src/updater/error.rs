//! Why an update check could not complete.

use std::{error::Error as StdError, fmt};

/// A failed update check, named by the first thing that went wrong.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Error {
    /// The system clock is unset, so TLS certificates cannot be validated.
    ClockNotSet,
    /// The feed is not a URL with a host.
    InvalidFeed(String),
    /// The release host's name does not resolve: no internet connection.
    Offline { host: String },
    /// The release host resolves but accepts no connection.
    Unreachable { host: String },
    /// The release service is up but failing.
    ServiceDown(u16),
    /// The release service refuses further requests for now.
    RateLimited,
    /// The request could not be built, sent or read; carries the cause chain,
    /// since reqwest's own message omits DNS, TLS or clock errors.
    Request(String),
    /// The release service answered with an unexpected HTTP status.
    Status(u16),
    /// The response did not describe a release.
    InvalidResponse(String),
    /// The latest release tag is not `v` followed by a semantic version.
    InvalidTag(String),
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ClockNotSet => formatter.write_str("the system clock is not set"),
            Self::InvalidFeed(feed) => write!(formatter, "release feed {feed:?} is not a URL"),
            Self::Offline { host } => {
                write!(formatter, "no internet connection: {host} does not resolve")
            }
            Self::Unreachable { host } => write!(formatter, "{host} is unreachable"),
            Self::ServiceDown(status) => {
                write!(formatter, "release service is down (HTTP {status})")
            }
            Self::RateLimited => {
                formatter.write_str("release service rate limit reached; try later")
            }
            Self::Request(cause) => write!(formatter, "release request failed: {cause}"),
            Self::Status(status) => write!(formatter, "release service answered HTTP {status}"),
            Self::InvalidResponse(cause) => write!(formatter, "not a release: {cause}"),
            Self::InvalidTag(tag) => {
                write!(formatter, "release tag {tag:?} is not v<semantic version>")
            }
        }
    }
}

impl StdError for Error {}

impl From<reqwest::Error> for Error {
    fn from(error: reqwest::Error) -> Self {
        let mut cause = error.to_string();
        let mut source = error.source();
        while let Some(next) = source {
            cause += &format!(": {next}");
            source = next.source();
        }
        Self::Request(cause)
    }
}
