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
    use std::time::Duration;

    use tokio::{task, time::timeout};

    use super::*;
    use crate::{
        events::Subscription,
        menu::transitions::{Phase, TransitionEvent, TransitionEventBus},
        updater::{
            Error, LATEST_RELEASE,
            fake::{FakeFeed, answer, release},
            installed,
        },
    };

    /// A transition reading `feed`, with a reporter and a subscription to
    /// what it reports.
    fn transition(
        feed: Option<String>,
    ) -> (
        UpdateCheck,
        Reporter<UpdateStatus>,
        Subscription<TransitionEvent>,
    ) {
        let events = TransitionEventBus::new();
        let reports = events.subscribe();
        let report = Reporter::new::<UpdateCheck>(&events);
        (UpdateCheck::new(&feed), report, reports)
    }

    async fn next(reports: &mut Subscription<TransitionEvent>) -> TransitionEvent {
        timeout(Duration::from_secs(5), reports.recv())
            .await
            .expect("the transition reported nothing")
            .unwrap()
    }

    async fn stopped(running: task::AbortHandle) {
        timeout(Duration::from_secs(2), async {
            while !running.is_finished() {
                task::yield_now().await;
            }
        })
        .await
        .expect("the check kept running");
    }

    #[test]
    fn the_product_checks_github_and_tests_run_offline() {
        assert_eq!(UpdateCheck::device(), Some(LATEST_RELEASE.to_owned()));
        assert_eq!(<UpdateCheck as Transition>::Settings::default(), None);
    }

    #[tokio::test]
    async fn without_a_feed_it_finishes_disabled_and_starts_nothing() {
        let (mut updates, report, mut reports) = transition(None);
        updates.start(report);

        assert!(updates.running.is_none());
        assert_eq!(
            next(&mut reports).await,
            TransitionEvent::new::<UpdateCheck>(Phase::Finished, UpdateStatus::Disabled)
        );
    }

    #[tokio::test]
    async fn reports_checking_then_each_result_as_its_status() {
        let installed = format!("v{}", installed::version());
        for (response, status) in [
            (answer("404 Not Found", ""), UpdateStatus::NoRelease),
            (release(&installed), UpdateStatus::UpToDate),
            (
                release("v99.0.0"),
                UpdateStatus::Available(Release {
                    version: semver::Version::new(99, 0, 0),
                    page: "https://example.invalid/v99.0.0".into(),
                }),
            ),
            (
                answer("503 Service Unavailable", ""),
                UpdateStatus::Failed(Error::ServiceDown(503)),
            ),
        ] {
            let feed = FakeFeed::answering(response);
            let (mut updates, report, mut reports) = transition(Some(feed.url.clone()));
            updates.start(report);

            assert_eq!(
                next(&mut reports).await,
                TransitionEvent::new::<UpdateCheck>(Phase::Progress, UpdateStatus::Checking)
            );
            assert_eq!(
                next(&mut reports).await,
                TransitionEvent::new::<UpdateCheck>(Phase::Finished, status)
            );
        }
    }

    #[tokio::test]
    async fn preflight_failures_become_failed_statuses() {
        let port = std::net::TcpListener::bind("127.0.0.1:0")
            .unwrap()
            .local_addr()
            .unwrap()
            .port();
        let (mut updates, report, mut reports) =
            transition(Some(format!("http://127.0.0.1:{port}/")));
        updates.start(report);

        next(&mut reports).await;
        assert_eq!(
            next(&mut reports).await,
            TransitionEvent::new::<UpdateCheck>(
                Phase::Finished,
                UpdateStatus::Failed(Error::Unreachable {
                    host: "127.0.0.1".into()
                })
            )
        );
    }

    #[tokio::test]
    async fn cancelling_aborts_the_running_check() {
        let feed = FakeFeed::silent();
        let (mut updates, report, mut reports) = transition(Some(feed.url.clone()));

        updates.start(report.clone());
        let running = updates.running.as_ref().unwrap().abort_handle();
        updates.cancel(report);

        stopped(running).await;
        assert!(updates.running.is_none());
        assert_eq!(
            next(&mut reports).await,
            TransitionEvent::new::<UpdateCheck>(Phase::Progress, UpdateStatus::Checking)
        );
        assert_eq!(
            next(&mut reports).await,
            TransitionEvent::new::<UpdateCheck>(Phase::Finished, UpdateStatus::NotChecked)
        );
    }

    #[tokio::test]
    async fn cancelling_with_nothing_running_still_reports_finished() {
        let (mut updates, report, mut reports) = transition(None);
        updates.cancel(report);
        assert_eq!(
            next(&mut reports).await,
            TransitionEvent::new::<UpdateCheck>(Phase::Finished, UpdateStatus::NotChecked)
        );
    }

    #[tokio::test]
    async fn starting_again_replaces_a_running_check() {
        let feed = FakeFeed::silent();
        let (mut updates, report, _reports) = transition(Some(feed.url.clone()));

        updates.start(report.clone());
        let first = updates.running.as_ref().unwrap().abort_handle();
        updates.start(report);

        stopped(first).await;
        assert!(!updates.running.as_ref().unwrap().is_finished());
    }

    #[tokio::test]
    async fn dropping_the_transition_stops_its_check() {
        let feed = FakeFeed::silent();
        let (mut updates, report, _reports) = transition(Some(feed.url.clone()));

        updates.start(report);
        let running = updates.running.as_ref().unwrap().abort_handle();
        drop(updates);

        stopped(running).await;
    }
}
