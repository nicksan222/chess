//! "Check for Updates" and "Install Update" behind the Update menu.
//!
//! Checking is blocking: the menu holds input from activation until the final
//! status arrives, and escape (`CancelCheck`) aborts the check. Installing is a
//! placeholder that finishes immediately.

use ::menu::Menu;
use logger::{info, warn};
use tokio::task::JoinHandle;

use super::{LATEST_RELEASE, Request, Settings, Status, Updates};
use crate::modules::{
    MissingDependency,
    connection::Connection,
    module::{Context, Module, Reporter},
};

/// Update discovery owned by one firmware instance.
pub(in crate::modules) struct Engine {
    updates: Updates,
    running: Option<JoinHandle<()>>,
}

impl Engine {
    fn check(&mut self, report: Reporter<Status>) {
        if !self.updates.is_enabled() {
            info!("update checks are disabled");
            report.finish(Status::Disabled);
            return;
        }
        report.progress(Status::Checking);
        let updates = self.updates.clone();
        let check = tokio::spawn(async move {
            let status = updates.check().await;
            match &status {
                Status::Failed(cause) => warn!("update check failed: {cause}"),
                status => info!("update check finished: {status:?}"),
            }
            report.finish(status);
        });
        if let Some(previous) = self.running.replace(check) {
            previous.abort();
        }
    }

    fn cancel(&mut self, report: &Reporter<Status>) {
        if let Some(running) = self.running.take() {
            running.abort();
        }
        info!("update check cancelled");
        report.finish(Status::NotChecked);
    }
}

impl Module for Engine {
    type Settings = Settings;
    type Status = Status;
    type Request = Request;
    type Facade = Updates;

    const MENU: Option<&'static Menu<'static, crate::modules::Request>> = Some(&super::MENU);

    fn device() -> Settings {
        Some(LATEST_RELEASE.to_owned())
    }

    fn new(feed: &Settings, context: &Context<'_, Status>) -> Result<Self, MissingDependency> {
        Ok(Self {
            updates: Updates::new(feed, context.get::<Connection>()?),
            running: None,
        })
    }

    fn facade(&self) -> Updates {
        self.updates.clone()
    }

    fn request(&mut self, request: Request, report: Reporter<Status>) {
        match request {
            Request::Check => self.check(report),
            Request::CancelCheck => self.cancel(&report),
            // Placeholder until installing is implemented.
            Request::Install => report.done(),
        }
    }
}

impl Drop for Engine {
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
        modules::{
            Config, Facades, ModuleEvent, ModuleEventBus, Modules, Phase,
            connection::fake::{Failure, FakeWifi, Operation},
            module::sealed::Registered,
            firmware::{
                Error, Release,
                fake::{FakeFeed, answer, release},
                installed,
            },
        },
    };

    const CHECK: crate::modules::Request = crate::modules::Request::Updates(Request::Check);
    const CANCEL: crate::modules::Request = crate::modules::Request::Updates(Request::CancelCheck);

    /// The update engine reading `feed`, with what it reports.
    struct Fixture {
        engine: Engine,
        events: ModuleEventBus,
        reports: Subscription<ModuleEvent>,
    }

    impl Fixture {
        /// Without Wi-Fi control, as in the offline configuration.
        fn new(feed: Option<&str>) -> Self {
            let (_, offline) = Modules::new(&Config::offline(), &ModuleEventBus::new()).unwrap();
            Self::with(feed, offline.connection.unwrap())
        }

        fn with(feed: Option<&str>, connection: Connection) -> Self {
            let feed = feed.map(str::to_owned);
            let events = ModuleEventBus::new();
            let reports = events.subscribe();
            let facades = Facades {
                connection: Some(connection),
                ..Facades::default()
            };
            let context = Context::new("firmware", &facades, reporter(&events, None));
            let engine = Engine::new(&feed, &context).unwrap();
            Self {
                engine,
                events,
                reports,
            }
        }

        fn request(&mut self, request: crate::modules::Request) {
            let crate::modules::Request::Updates(inner) = request else {
                panic!("{request:?} is not an update request");
            };
            let report = reporter(&self.events, Some(request));
            self.engine.request(inner, report);
        }

        async fn next(&mut self) -> ModuleEvent {
            timeout(Duration::from_secs(5), self.reports.recv())
                .await
                .expect("the module reported nothing")
                .unwrap()
        }

        fn running(&self) -> task::AbortHandle {
            self.engine.running.as_ref().unwrap().abort_handle()
        }
    }

    fn reporter(
        events: &ModuleEventBus,
        request: Option<crate::modules::Request>,
    ) -> Reporter<Status> {
        Reporter::new(events, request, <Updates as Registered>::wrap)
    }

    fn event(request: crate::modules::Request, phase: Phase, status: Status) -> ModuleEvent {
        ModuleEvent::new::<Updates>(Some(request), phase, status)
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
        assert_eq!(Engine::device(), Some(LATEST_RELEASE.to_owned()));
        assert_eq!(Settings::default(), None);
    }

    #[test]
    fn registered_before_its_connection_it_fails_naming_both_modules() {
        let events = ModuleEventBus::new();
        let empty = Facades::default();
        let context = Context::new("firmware", &empty, reporter(&events, None));

        let Err(error) = Engine::new(&None, &context) else {
            panic!("built without its connection dependency");
        };
        assert_eq!(
            error.to_string(),
            "module `firmware` uses `connection`, which is not built yet; \
             register `connection` before `firmware` in `modules!`"
        );
        assert_eq!(format!("{error:?}"), error.to_string(), "unwrap reads well");
    }

    #[tokio::test]
    async fn without_a_feed_it_finishes_disabled_and_starts_nothing() {
        let mut updates = Fixture::new(None);
        updates.request(CHECK);

        assert!(updates.engine.running.is_none());
        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Finished, Status::Disabled)
        );
    }

    #[tokio::test]
    async fn reports_checking_then_each_result_as_its_status() {
        let installed = format!("v{}", installed::version());
        for (response, status) in [
            (answer("404 Not Found", ""), Status::NoRelease),
            (release(&installed), Status::UpToDate),
            (
                release("v99.0.0"),
                Status::Available(Release {
                    version: semver::Version::new(99, 0, 0),
                    page: "https://example.invalid/v99.0.0".into(),
                }),
            ),
            (
                answer("503 Service Unavailable", ""),
                Status::Failed(Error::ServiceDown(503)),
            ),
        ] {
            let feed = FakeFeed::answering(response);
            let mut updates = Fixture::new(Some(feed.url.as_str()));
            updates.request(CHECK);

            assert_eq!(
                updates.next().await,
                event(CHECK, Phase::Progress, Status::Checking)
            );
            assert_eq!(updates.next().await, event(CHECK, Phase::Finished, status));
        }
    }

    #[tokio::test]
    async fn disconnected_wifi_finishes_offline_without_asking_the_feed() {
        let feed = FakeFeed::answering(release("v99.0.0"));
        let mut updates = Fixture::with(
            Some(feed.url.as_str()),
            Connection::fake(FakeWifi::default()),
        );
        updates.request(CHECK);

        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Progress, Status::Checking)
        );
        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Finished, Status::WifiDisconnected)
        );
        assert!(feed.requests().is_empty(), "{:?}", feed.requests());
    }

    #[tokio::test]
    async fn unknown_wifi_state_still_checks_the_feed() {
        let feed = FakeFeed::answering(answer("404 Not Found", ""));
        let wifi = FakeWifi::default();
        wifi.fail_next(Operation::Radio, Failure::Timeout);
        let mut updates = Fixture::with(Some(feed.url.as_str()), Connection::fake(wifi));
        updates.request(CHECK);

        updates.next().await;
        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Finished, Status::NoRelease)
        );
        assert_eq!(feed.requests().len(), 1);
    }

    #[tokio::test(start_paused = true)]
    async fn a_stalled_wifi_lookup_gives_up_after_one_probe() {
        let stalled = Connection::fake(FakeWifi::default().stalled());
        let started = tokio::time::Instant::now();

        assert!(!crate::modules::firmware::wifi_disconnected(&stalled).await);
        assert_eq!(started.elapsed(), crate::modules::firmware::preflight::PROBE);
        assert!(
            crate::modules::firmware::wifi_disconnected(&Connection::fake(FakeWifi::default())).await
        );
    }

    #[tokio::test]
    async fn connected_wifi_checks_the_feed() {
        let feed = FakeFeed::answering(answer("404 Not Found", ""));
        let mut updates = Fixture::with(
            Some(feed.url.as_str()),
            Connection::fake(FakeWifi::default().with_active_client("Home")),
        );
        updates.request(CHECK);

        updates.next().await;
        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Finished, Status::NoRelease)
        );
        assert_eq!(feed.requests().len(), 1);
    }

    #[tokio::test]
    async fn preflight_failures_become_failed_statuses() {
        let port = std::net::TcpListener::bind("127.0.0.1:0")
            .unwrap()
            .local_addr()
            .unwrap()
            .port();
        let mut updates = Fixture::new(Some(format!("http://127.0.0.1:{port}/").as_str()));
        updates.request(CHECK);

        updates.next().await;
        assert_eq!(
            updates.next().await,
            event(
                CHECK,
                Phase::Finished,
                Status::Failed(Error::Unreachable {
                    host: "127.0.0.1".into()
                })
            )
        );
    }

    #[tokio::test]
    async fn cancelling_aborts_the_running_check() {
        let feed = FakeFeed::silent();
        let mut updates = Fixture::new(Some(feed.url.as_str()));

        updates.request(CHECK);
        let running = updates.running();
        updates.request(CANCEL);

        stopped(running).await;
        assert!(updates.engine.running.is_none());
        assert_eq!(
            updates.next().await,
            event(CHECK, Phase::Progress, Status::Checking)
        );
        assert_eq!(
            updates.next().await,
            event(CANCEL, Phase::Finished, Status::NotChecked)
        );
    }

    #[tokio::test]
    async fn cancelling_with_nothing_running_still_reports_finished() {
        let mut updates = Fixture::new(None);
        updates.request(CANCEL);
        assert_eq!(
            updates.next().await,
            event(CANCEL, Phase::Finished, Status::NotChecked)
        );
    }

    #[tokio::test]
    async fn starting_again_replaces_a_running_check() {
        let feed = FakeFeed::silent();
        let mut updates = Fixture::new(Some(feed.url.as_str()));

        updates.request(CHECK);
        let first = updates.running();
        updates.request(CHECK);

        stopped(first).await;
        assert!(!updates.engine.running.as_ref().unwrap().is_finished());
    }

    #[tokio::test]
    async fn dropping_the_module_stops_its_check() {
        let feed = FakeFeed::silent();
        let mut updates = Fixture::new(Some(feed.url.as_str()));

        updates.request(CHECK);
        let running = updates.running();
        drop(updates);

        stopped(running).await;
    }

    #[tokio::test]
    async fn installing_is_a_placeholder_that_finishes_at_once() {
        let install = crate::modules::Request::Updates(Request::Install);
        let mut updates = Fixture::new(None);
        updates.request(install);
        let done = updates.next().await;
        assert_eq!(done.phase, Phase::Finished);
        assert_eq!(done.status, None, "the check result stays presented");
    }
}
