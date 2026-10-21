//! GitHub Releases, where the Firmware workflow publishes `v*` tags.

use std::time::Duration;

use reqwest::{Client, StatusCode, header::ACCEPT};
use tokio::task;

use super::{Error, installed};

/// Newest non-draft, non-prerelease release of this repository.
pub const LATEST_RELEASE: &str = "https://api.github.com/repos/nicksan222/chess/releases/latest";

/// The tag and page of the latest release at `feed`, or `None` when GitHub
/// answers 404, as it does before the first stable release.
pub(super) async fn latest(feed: &str) -> Result<Option<(String, String)>, Error> {
    // Loading the system trust store reads files, so keep it off the event loop.
    let client = task::spawn_blocking(client)
        .await
        .map_err(|error| Error::Request(error.to_string()))??;
    let response = client
        .get(feed)
        .header(ACCEPT, "application/vnd.github+json")
        .send()
        .await?;
    match response.status() {
        status if status.is_success() => {}
        StatusCode::NOT_FOUND => return Ok(None),
        // GitHub answers 403 or 429 once the unauthenticated quota is spent.
        StatusCode::FORBIDDEN | StatusCode::TOO_MANY_REQUESTS => return Err(Error::RateLimited),
        status if status.is_server_error() => return Err(Error::ServiceDown(status.as_u16())),
        status => return Err(Error::Status(status.as_u16())),
    }
    let body = response.bytes().await?;
    let release: serde_json::Value =
        serde_json::from_slice(&body).map_err(|error| Error::InvalidResponse(error.to_string()))?;
    match (release["tag_name"].as_str(), release["html_url"].as_str()) {
        (Some(tag), Some(page)) => Ok(Some((tag.to_owned(), page.to_owned()))),
        _ => Err(Error::InvalidResponse(release.to_string())),
    }
}

fn client() -> Result<Client, Error> {
    // reqwest is built without a bundled crypto provider; ring is the one linked.
    let _ = rustls::crypto::ring::default_provider().install_default();
    Ok(Client::builder()
        // GitHub rejects API requests without a user agent.
        .user_agent(format!("{}/{}", installed::NAME, installed::version()))
        .timeout(Duration::from_secs(15))
        .build()?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::updater::fake::{FakeFeed, answer, release};

    #[tokio::test]
    async fn asks_for_the_github_api_as_this_firmware() {
        let feed = FakeFeed::answering(release("v1.0.0"));
        latest(&feed.url).await.unwrap();

        let requests = feed.requests();
        assert_eq!(requests.len(), 1);
        let request = requests[0].to_ascii_lowercase();
        assert!(request.starts_with("get /releases/latest "), "{request}");
        assert!(
            request.contains("accept: application/vnd.github+json"),
            "{request}"
        );
        let agent = format!("user-agent: {}/{}", installed::NAME, installed::version());
        assert!(request.contains(&agent), "{request}");
    }

    #[tokio::test]
    async fn returns_the_tag_and_page_of_the_latest_release() {
        let feed = FakeFeed::answering(release("v1.2.3"));
        assert_eq!(
            latest(&feed.url).await,
            Ok(Some((
                "v1.2.3".into(),
                "https://example.invalid/v1.2.3".into()
            )))
        );
    }

    #[tokio::test]
    async fn no_release_yet_is_not_an_error() {
        let feed = FakeFeed::answering(answer("404 Not Found", ""));
        assert_eq!(latest(&feed.url).await, Ok(None));
    }

    #[tokio::test]
    async fn classifies_failing_statuses() {
        for (status, expected) in [
            ("403 Forbidden", Error::RateLimited),
            ("429 Too Many Requests", Error::RateLimited),
            ("500 Internal Server Error", Error::ServiceDown(500)),
            ("502 Bad Gateway", Error::ServiceDown(502)),
            ("401 Unauthorized", Error::Status(401)),
        ] {
            let feed = FakeFeed::answering(answer(status, ""));
            assert_eq!(latest(&feed.url).await, Err(expected), "{status}");
        }
    }

    #[tokio::test]
    async fn rejects_answers_that_are_not_releases() {
        for body in [
            "not json",
            r#"{"tag_name": "v1.0.0"}"#,
            r#"{"html_url": "https://example.invalid"}"#,
            r#"{"tag_name": 1, "html_url": "https://example.invalid"}"#,
        ] {
            let feed = FakeFeed::answering(answer("200 OK", body));
            assert!(
                matches!(latest(&feed.url).await, Err(Error::InvalidResponse(_))),
                "{body}"
            );
        }
    }
}
