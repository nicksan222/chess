//! "Check for Updates": asks GitHub Releases whether newer firmware is
//! published and reports it.
//!
//! A blocking transition: the menu holds input from activation until the final
//! status arrives, and escape (`CancelUpdateCheck`) aborts the check.

use std::{cmp::Ordering, error::Error, time::Duration};

use logger::{info, warn};
use reqwest::{Client, StatusCode, header::ACCEPT};
use semver::Version;
use tokio::task::{self, JoinHandle};

use super::{Reporter, Transition};
use crate::menu::Request;

/// Newest non-draft, non-prerelease release; tags are `v<Cargo version>`.
const GITHUB_RELEASES: &str = "https://api.github.com/repos/nicksan222/chess/releases/latest";

type BoxError = Box<dyn Error + Send + Sync>;

/// Update discovery owned by one firmware instance.
pub struct UpdateCheck {
    feed: Option<String>,
    running: Option<JoinHandle<()>>,
}

/// Progress of "Check for Updates", as presented in the firmware snapshot.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub enum UpdateStatus {
    /// No check has completed since startup, or the last one was cancelled.
    #[default]
    NotChecked,
    /// A check is running while the menu holds input.
    Checking,
    /// This firmware instance is configured without a release feed.
    Disabled,
    /// The feed answered 404, as GitHub does before the first stable release.
    NoRelease,
    /// The latest release is not newer than the running firmware.
    UpToDate,
    /// A newer release and its page.
    Available { version: Version, page: String },
    /// The check could not complete; carries the cause chain.
    Failed(String),
}

impl Transition for UpdateCheck {
    const REQUEST: Request = Request::CheckForUpdates;
    const CANCEL: Option<Request> = Some(Request::CancelUpdateCheck);

    /// The release endpoint; `None`, the default, disables checks.
    type Settings = Option<String>;
    type Status = UpdateStatus;

    fn device() -> Self::Settings {
        Some(GITHUB_RELEASES.to_owned())
    }

    fn new(feed: &Self::Settings) -> Self {
        Self {
            feed: feed.clone(),
            running: None,
        }
    }

    fn start(&mut self, report: Reporter<UpdateStatus>) {
        let Some(feed) = self.feed.clone() else {
            info!("update checks are disabled");
            report.finish(UpdateStatus::Disabled);
            return;
        };
        report.progress(UpdateStatus::Checking);
        let check = tokio::spawn(async move {
            let status = check(&feed, &running_version())
                .await
                .unwrap_or_else(|error| UpdateStatus::Failed(chain(&*error)));
            match &status {
                UpdateStatus::Failed(cause) => warn!("update check failed: {cause}"),
                status => info!("update check finished: {status:?}"),
            }
            report.finish(status);
        });
        if let Some(previous) = self.running.replace(check) {
            previous.abort();
        }
    }

    fn cancel(&mut self, report: Reporter<UpdateStatus>) {
        if let Some(running) = self.running.take() {
            running.abort();
        }
        info!("update check cancelled");
        report.finish(UpdateStatus::NotChecked);
    }
}

impl Drop for UpdateCheck {
    // The firmware loop owns this, so stopping the loop cancels a running check.
    fn drop(&mut self) {
        if let Some(running) = &self.running {
            running.abort();
        }
    }
}

async fn check(feed: &str, current: &Version) -> Result<UpdateStatus, BoxError> {
    // Loading the system trust store reads files, so keep it off the event loop.
    let response = task::spawn_blocking(client)
        .await??
        .get(feed)
        .header(ACCEPT, "application/vnd.github+json")
        .send()
        .await?;
    if response.status() == StatusCode::NOT_FOUND {
        return Ok(UpdateStatus::NoRelease);
    }
    let body = response.error_for_status()?.bytes().await?;
    let release: serde_json::Value = serde_json::from_slice(&body)?;
    let (Some(tag), Some(page)) = (release["tag_name"].as_str(), release["html_url"].as_str())
    else {
        return Err(format!("not a GitHub release: {release}").into());
    };
    Ok(match newer(tag, current)? {
        Some(version) => UpdateStatus::Available {
            version,
            page: page.to_owned(),
        },
        None => UpdateStatus::UpToDate,
    })
}

fn client() -> Result<Client, BoxError> {
    // reqwest is built without a bundled crypto provider; ring is the one linked.
    let _ = rustls::crypto::ring::default_provider().install_default();
    Ok(Client::builder()
        // GitHub rejects API requests without a user agent.
        .user_agent(concat!("firmware/", env!("CARGO_PKG_VERSION")))
        .timeout(Duration::from_secs(15))
        .build()?)
}

fn running_version() -> Version {
    Version::parse(env!("CARGO_PKG_VERSION")).expect("Cargo package versions are semantic")
}

/// The tagged version, if it is newer than `current`. Build metadata is ignored.
fn newer(tag: &str, current: &Version) -> Result<Option<Version>, String> {
    let version = tag
        .strip_prefix('v')
        .and_then(|version| Version::parse(version).ok())
        .ok_or_else(|| format!("release tag {tag:?} is not v<semantic version>"))?;
    Ok((version.cmp_precedence(current) == Ordering::Greater).then_some(version))
}

/// reqwest's own message omits causes such as DNS, TLS or clock errors.
fn chain(error: &(dyn Error + 'static)) -> String {
    let mut message = error.to_string();
    let mut source = error.source();
    while let Some(cause) = source {
        message += &format!(": {cause}");
        source = cause.source();
    }
    message
}

#[cfg(test)]
mod tests {
    use std::{
        io::{Read, Write},
        net::TcpListener,
        thread,
    };

    use super::*;
    use crate::menu::transitions::{TransitionEvent, TransitionEventBus};

    /// Serves `response` to every connection on a local port.
    fn feed(response: &'static str) -> String {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let url = format!("http://{}/releases/latest", listener.local_addr().unwrap());
        thread::spawn(move || {
            for mut stream in listener.incoming().flatten() {
                let mut request = [0; 4096];
                let _ = stream.read(&mut request);
                let _ = stream.write_all(response.as_bytes());
            }
        });
        url
    }

    fn release(tag: &str) -> &'static str {
        let body =
            format!(r#"{{"tag_name": "{tag}", "html_url": "https://example.invalid/{tag}"}}"#);
        format!(
            "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        )
        .leak()
    }

    const NOT_FOUND: &str =
        "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";

    #[tokio::test]
    async fn reports_what_the_feed_publishes() {
        let current = Version::new(1, 2, 0);
        assert_eq!(
            check(&feed(NOT_FOUND), &current).await.unwrap(),
            UpdateStatus::NoRelease
        );
        assert_eq!(
            check(&feed(release("v1.2.0")), &current).await.unwrap(),
            UpdateStatus::UpToDate
        );
        assert_eq!(
            check(&feed(release("v1.3.0")), &current).await.unwrap(),
            UpdateStatus::Available {
                version: Version::new(1, 3, 0),
                page: "https://example.invalid/v1.3.0".into(),
            }
        );
    }

    #[tokio::test]
    async fn failures_are_errors_not_up_to_date() {
        let current = Version::new(1, 0, 0);
        let unavailable =
            "HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";
        let error = check(&feed(unavailable), &current).await.unwrap_err();
        assert!(chain(&*error).contains("503"), "{error}");
        let malformed = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}";
        assert!(check(&feed(malformed), &current).await.is_err());
    }

    #[tokio::test]
    async fn cancelling_aborts_the_running_check() {
        // Accepts connections but never answers, so the check stays in flight.
        let silent = TcpListener::bind("127.0.0.1:0").unwrap();
        let feed = Some(format!("http://{}/", silent.local_addr().unwrap()));
        let events = TransitionEventBus::new();
        let mut reports = events.subscribe();
        let report = Reporter::new::<UpdateCheck>(&events);
        let mut updates = UpdateCheck::new(&feed);

        updates.start(report.clone());
        let running = updates.running.as_ref().unwrap().abort_handle();
        updates.cancel(report);

        tokio::time::timeout(Duration::from_secs(2), async {
            while !running.is_finished() {
                task::yield_now().await;
            }
        })
        .await
        .unwrap();
        assert_eq!(
            reports.try_recv().unwrap(),
            Some(TransitionEvent::progress::<UpdateCheck>(
                UpdateStatus::Checking
            ))
        );
        assert_eq!(
            reports.try_recv().unwrap(),
            Some(TransitionEvent::finished::<UpdateCheck>(
                UpdateStatus::NotChecked
            ))
        );
    }

    #[test]
    fn only_a_higher_precedence_tag_is_newer() {
        let current = Version::new(1, 2, 0);
        assert_eq!(newer("v1.3.0", &current), Ok(Some(Version::new(1, 3, 0))));
        for tag in ["v1.2.0", "v1.1.9", "v1.2.0+build.7", "v1.2.0-rc.1"] {
            assert_eq!(newer(tag, &current), Ok(None), "{tag}");
        }
        let rc = Version::parse("1.2.0-rc.1").unwrap();
        assert_eq!(newer("v1.2.0", &rc), Ok(Some(current)));
    }

    #[test]
    fn rejects_tags_that_are_not_v_semver() {
        for tag in ["1.3.0", "v1.3", "latest"] {
            assert!(newer(tag, &Version::new(1, 0, 0)).is_err(), "{tag}");
        }
    }
}
