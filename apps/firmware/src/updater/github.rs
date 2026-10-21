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
