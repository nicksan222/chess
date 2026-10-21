//! "Check for Updates": runs the [`Updater`] check and presents its result.
//!
//! A blocking transition: the menu holds input from activation until the final
//! status arrives, and escape (`CancelUpdateCheck`) aborts the check. Update
//! logic lives in [`crate::updater`].

use logger::{info, warn};
use tokio::task::JoinHandle;

use super::{Reporter, Transition};
use crate::{
    menu::Request,
    updater::{Availability, Error, Release, Updater},
};

/// Update discovery owned by one firmware instance.
pub struct UpdateCheck {
    updater: Option<Updater>,
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
    /// Nothing is published yet.
    NoRelease,
    /// The latest release is not newer than the installed firmware.
    UpToDate,
    /// A newer release.
    Available(Release),
    /// The check could not complete, named by its first failed step.
    Failed(Error),
}

impl Transition for UpdateCheck {
    const REQUEST: Request = Request::CheckForUpdates;
    const CANCEL: Option<Request> = Some(Request::CancelUpdateCheck);

    /// The release feed; `None`, the default, disables checks.
    type Settings = Option<String>;
    type Status = UpdateStatus;

    fn device() -> Self::Settings {
        Some(crate::updater::LATEST_RELEASE.to_owned())
    }

    fn new(feed: &Self::Settings) -> Self {
        Self {
            updater: feed.as_deref().map(Updater::new),
            running: None,
        }
    }

    fn start(&mut self, report: Reporter<UpdateStatus>) {
        let Some(updater) = self.updater.clone() else {
            info!("update checks are disabled");
            report.finish(UpdateStatus::Disabled);
            return;
        };
        report.progress(UpdateStatus::Checking);
        let check = tokio::spawn(async move {
            let status = match updater.check().await {
                Ok(Availability::NoRelease) => UpdateStatus::NoRelease,
                Ok(Availability::UpToDate) => UpdateStatus::UpToDate,
                Ok(Availability::Available(release)) => UpdateStatus::Available(release),
                Err(error) => UpdateStatus::Failed(error),
            };
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

#[cfg(test)]
mod tests {
    use std::{net::TcpListener, time::Duration};

    use tokio::task;

    use super::*;
    use crate::menu::transitions::{TransitionEvent, TransitionEventBus};

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
}
