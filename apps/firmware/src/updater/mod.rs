//! The local firmware and its updates: what is installed, what is published,
//! and whether newer firmware is available.
//!
//! Presentation-agnostic: menus and displays use [`Updater`] and its typed
//! results. Installing an update is not implemented.

mod error;
mod github;
pub mod installed;
mod release;

pub use error::Error;
pub use github::LATEST_RELEASE;
pub use release::{Availability, Release};

/// Checks a release feed for firmware newer than the installed one.
#[derive(Clone, Debug)]
pub struct Updater {
    feed: String,
}

impl Updater {
    /// Checks the GitHub Releases feed of this repository.
    pub fn github() -> Self {
        Self::new(LATEST_RELEASE)
    }

    /// Checks a GitHub-compatible "latest release" endpoint at `feed`.
    pub fn new(feed: impl Into<String>) -> Self {
        Self { feed: feed.into() }
    }

    /// Compares the latest published release with the installed firmware.
    pub async fn check(&self) -> Result<Availability, Error> {
        match github::latest(&self.feed).await? {
            None => Ok(Availability::NoRelease),
            Some((tag, page)) => Availability::of(&tag, &page, &installed::version()),
        }
    }
}

#[cfg(test)]
mod tests {
    use std::{
        io::{Read, Write},
        net::TcpListener,
        thread,
    };

    use semver::Version;

    use super::*;

    /// Serves `response` to every connection on a local port.
    fn feed(response: String) -> Updater {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let url = format!("http://{}/releases/latest", listener.local_addr().unwrap());
        thread::spawn(move || {
            for mut stream in listener.incoming().flatten() {
                let _ = stream.read(&mut [0; 4096]);
                let _ = stream.write_all(response.as_bytes());
            }
        });
        Updater::new(url)
    }

    fn answer(status: &str, body: &str) -> String {
        format!(
            "HTTP/1.1 {status}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        )
    }

    fn release(tag: &str) -> String {
        answer(
            "200 OK",
            &format!(r#"{{"tag_name": "{tag}", "html_url": "https://example.invalid/{tag}"}}"#),
        )
    }

    #[tokio::test]
    async fn reports_what_the_feed_publishes() {
        assert_eq!(
            feed(answer("404 Not Found", "")).check().await,
            Ok(Availability::NoRelease)
        );
        let installed = installed::version();
        assert_eq!(
            feed(release(&format!("v{installed}"))).check().await,
            Ok(Availability::UpToDate)
        );
        assert_eq!(
            feed(release("v99.0.0")).check().await,
            Ok(Availability::Available(Release {
                version: Version::new(99, 0, 0),
                page: "https://example.invalid/v99.0.0".into(),
            }))
        );
    }

    #[tokio::test]
    async fn failures_are_errors_not_up_to_date() {
        assert_eq!(
            feed(answer("503 Service Unavailable", "")).check().await,
            Err(Error::Status(503))
        );
        assert!(matches!(
            feed(answer("200 OK", "{}")).check().await,
            Err(Error::InvalidResponse(_))
        ));
        assert_eq!(
            feed(release("latest")).check().await,
            Err(Error::InvalidTag("latest".into()))
        );
    }
}
