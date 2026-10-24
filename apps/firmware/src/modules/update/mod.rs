//! The local firmware and its updates: what is installed, what is published,
//! and whether newer firmware is available.
//!
//! Presentation-agnostic: menus and displays use [`Update`] and its typed
//! results. A check first asks the [`Connection`] module whether Wi-Fi is
//! definitively disconnected, then runs preflight checks, cheapest first, and
//! asks the GitHub Releases API for the latest stable release. Installing an
//! update is not implemented.

mod engine;
mod error;
#[cfg(test)]
mod fake;
mod github;
mod installed;
mod preflight;
mod release;
mod updater;

use ::menu::{Menu, MenuItem};
use tokio::time::timeout;

use super::connection::{Connection, Link};
use github::LATEST_RELEASE;
use release::Availability;
use updater::Updater;

pub(super) use engine::Engine;
pub use error::Error;
pub use installed::{NAME, version};
pub use release::Release;

/// The release feed; `None`, the default, disables checks.
pub type Settings = Option<String>;

/// Progress of "Check for Updates", as presented in the firmware snapshot.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub enum Status {
    /// No check has completed since startup, or the last one was cancelled.
    #[default]
    NotChecked,
    /// A check is running while the menu holds input.
    Checking,
    /// This firmware instance is configured without a release feed.
    Disabled,
    /// Wi-Fi is confirmed disconnected, so no check was attempted.
    WifiDisconnected,
    /// Nothing is published yet.
    NoRelease,
    /// The latest release is not newer than the installed firmware.
    UpToDate,
    /// A newer release.
    Available(Release),
    /// The check could not complete, named by its first failed step.
    Failed(Error),
}

/// Requests from the Update menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Request {
    /// Check whether a software update is available; blocking.
    Check,
    /// Abandon a running check; the escape action of `Check`.
    CancelCheck,
    /// Start the externally managed update flow; a placeholder.
    Install,
}

/// Software update controls.
pub static MENU: Menu<'static, super::Request> = Menu::new(
    "Update",
    &[
        MenuItem::blocking_action(
            "Check for Updates",
            super::Request::Update(Request::Check),
            super::Request::Update(Request::CancelCheck),
        ),
        MenuItem::action("Install Update", super::Request::Update(Request::Install)),
    ],
);

/// Firmware update discovery.
#[derive(Clone)]
pub struct Update {
    updater: Option<Updater>,
    connection: Connection,
}

impl Update {
    fn new(feed: &Settings, connection: Connection) -> Self {
        Self {
            updater: feed.as_deref().map(Updater::new),
            connection,
        }
    }

    /// Whether this instance has a release feed to check.
    pub fn is_enabled(&self) -> bool {
        self.updater.is_some()
    }

    /// Compares the latest published release with the installed firmware.
    ///
    /// Ends `Disabled` without a feed and `WifiDisconnected` when the
    /// connection module confirms Wi-Fi is disconnected. When Wi-Fi state is
    /// unknown, as without Wi-Fi control, after an error, or when the answer
    /// takes longer than a preflight probe, the check runs and its preflight
    /// names any failure.
    pub async fn check(&self) -> Status {
        let Some(updater) = &self.updater else {
            return Status::Disabled;
        };
        if wifi_disconnected(&self.connection).await {
            return Status::WifiDisconnected;
        }
        match updater.check().await {
            Ok(Availability::NoRelease) => Status::NoRelease,
            Ok(Availability::UpToDate) => Status::UpToDate,
            Ok(Availability::Available(release)) => Status::Available(release),
            Err(error) => Status::Failed(error),
        }
    }
}

/// Whether `connection` confirms, within one preflight probe, that Wi-Fi is
/// disconnected. Errors and slow answers are not a confirmation.
async fn wifi_disconnected(connection: &Connection) -> bool {
    matches!(
        timeout(preflight::PROBE, connection.status()).await,
        Ok(Ok(Link::Disconnected))
    )
}
