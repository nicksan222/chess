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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_failure_reads_as_a_sentence_naming_its_cause() {
        for (error, message) in [
            (Error::ClockNotSet, "the system clock is not set"),
            (
                Error::Offline {
                    host: "api.github.com".into(),
                },
                "no internet connection: api.github.com does not resolve",
            ),
            (
                Error::Unreachable {
                    host: "api.github.com".into(),
                },
                "api.github.com is unreachable",
            ),
            (
                Error::ServiceDown(503),
                "release service is down (HTTP 503)",
            ),
            (
                Error::RateLimited,
                "release service rate limit reached; try later",
            ),
            (Error::Status(401), "release service answered HTTP 401"),
            (
                Error::InvalidTag("latest".into()),
                r#"release tag "latest" is not v<semantic version>"#,
            ),
        ] {
            assert_eq!(error.to_string(), message);
        }
    }

    #[tokio::test]
    async fn request_failures_keep_their_cause_chain() {
        // reqwest panics without a crypto provider; the product's client
        // installs ring the same way, and test order must not matter.
        let _ = rustls::crypto::ring::default_provider().install_default();
        // A refused connection: reqwest's own message hides why.
        let port = std::net::TcpListener::bind("127.0.0.1:0")
            .unwrap()
            .local_addr()
            .unwrap()
            .port();
        let failure = reqwest::get(format!("http://127.0.0.1:{port}/"))
            .await
            .unwrap_err();
        let top = failure.to_string();
        let Error::Request(chain) = Error::from(failure) else {
            panic!("not a request error");
        };
        assert!(chain.starts_with(&top), "{chain}");
        assert!(chain.len() > top.len(), "the cause is missing: {chain}");
    }
}
