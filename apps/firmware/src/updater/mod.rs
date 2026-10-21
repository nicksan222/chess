//! The local firmware and its updates: what is installed, what is published,
//! and whether newer firmware is available.
//!
//! Presentation-agnostic: menus and displays use [`Updater`] and its typed
//! results. Installing an update is not implemented.

mod error;
#[cfg(test)]
pub(crate) mod fake;
mod github;
pub mod installed;
mod preflight;
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

    /// Compares the latest published release with the installed firmware,
    /// after checking the clock, the internet connection and the release host.
    pub async fn check(&self) -> Result<Availability, Error> {
        preflight::run(&self.feed).await?;
        match github::latest(&self.feed).await? {
            None => Ok(Availability::NoRelease),
            Some((tag, page)) => Availability::of(&tag, &page, &installed::version()),
        }
    }
}

#[cfg(test)]
mod tests {
    use semver::Version;

    use super::{
        fake::{FakeFeed, answer, release},
        *,
    };

    fn check(response: String) -> Updater {
        Updater::new(FakeFeed::answering(response).url)
    }

    #[tokio::test]
    async fn reports_what_the_feed_publishes() {
        assert_eq!(
            check(answer("404 Not Found", "")).check().await,
            Ok(Availability::NoRelease)
        );
        let installed = installed::version();
        assert_eq!(
            check(release(&format!("v{installed}"))).check().await,
            Ok(Availability::UpToDate)
        );
        assert_eq!(
            check(release("v99.0.0")).check().await,
            Ok(Availability::Available(Release {
                version: Version::new(99, 0, 0),
                page: "https://example.invalid/v99.0.0".into(),
            }))
        );
    }

    #[tokio::test]
    async fn failures_are_errors_not_up_to_date() {
        assert_eq!(
            check(answer("503 Service Unavailable", "")).check().await,
            Err(Error::ServiceDown(503))
        );
        assert_eq!(
            check(answer("429 Too Many Requests", "")).check().await,
            Err(Error::RateLimited)
        );
        assert_eq!(
            check(answer("400 Bad Request", "")).check().await,
            Err(Error::Status(400))
        );
        assert!(matches!(
            check(answer("200 OK", "{}")).check().await,
            Err(Error::InvalidResponse(_))
        ));
        assert_eq!(
            check(release("latest")).check().await,
            Err(Error::InvalidTag("latest".into()))
        );
    }

    #[tokio::test]
    async fn preflight_failures_stop_before_any_request() {
        let port = std::net::TcpListener::bind("127.0.0.1:0")
            .unwrap()
            .local_addr()
            .unwrap()
            .port();
        assert_eq!(
            Updater::new(format!("http://127.0.0.1:{port}/"))
                .check()
                .await,
            Err(Error::Unreachable {
                host: "127.0.0.1".into()
            })
        );
    }

    #[test]
    fn the_product_checks_this_repositorys_github_releases() {
        assert_eq!(Updater::github().feed, LATEST_RELEASE);
        assert!(
            LATEST_RELEASE.starts_with("https://api.github.com/repos/nicksan222/chess/"),
            "{LATEST_RELEASE}"
        );
    }
}
