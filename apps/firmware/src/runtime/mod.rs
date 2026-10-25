//! The application event loop, shared by the executable and E2E harness.

mod state;

use std::io;

use tokio::{runtime::Handle, task::JoinHandle};

use crate::{
    events::{ReceiveError, StatePublisher, StateSubscription},
    hardware::HardwareEventBus,
    modules::{Config, Facade, Facades, ModuleEventBus, Modules},
};
use state::State;

pub use state::Snapshot;

/// Owns one running firmware instance. Dropping it stops its event loop.
pub struct Firmware {
    events: HardwareEventBus,
    reports: ModuleEventBus,
    facades: Facades,
    updates: StateSubscription<Snapshot>,
    worker: JoinHandle<Result<(), ReceiveError>>,
}

impl std::fmt::Debug for Firmware {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("Firmware")
            .field("snapshot", &self.updates.current())
            .finish_non_exhaustive()
    }
}

impl Firmware {
    /// Starts the real application loop with no physical adapters attached.
    /// Hardware workers attach through `events()`; tests inject through it too.
    ///
    /// # Errors
    ///
    /// Fails without an active async runtime or when module startup fails.
    pub fn start() -> io::Result<Self> {
        Self::start_with(&Config::device())
    }

    /// Starts the loop with explicit module settings. Stopping the loop
    /// cancels background work its modules started. Fails without an async
    /// runtime or when a module uses one registered after it.
    ///
    /// # Errors
    ///
    /// Fails as described above.
    pub fn start_with(config: &Config) -> io::Result<Self> {
        let runtime = Handle::try_current().map_err(|error| {
            io::Error::other(format!(
                "starting firmware requires an async runtime: {error}"
            ))
        })?;
        let events = HardwareEventBus::new();
        // Subscribe before returning so even the first injected event is handled.
        let mut subscription = events.subscribe();
        let reports = ModuleEventBus::new();
        // Likewise before building, so reports from startup work are kept.
        let mut reported = reports.subscribe();
        let (modules, facades) = Modules::new(config, &reports).map_err(io::Error::other)?;
        let mut state = State::new(modules);
        let updates = StatePublisher::new(State::initial_snapshot());
        let receiver = updates.subscribe();
        let worker = runtime.spawn(async move {
            loop {
                tokio::select! {
                    // Results first, so a finished operation unblocks the menu
                    // before the next input is interpreted.
                    biased;
                    event = reported.recv() => {
                        let event = event?;
                        updates.modify(|snapshot| state.report(event, snapshot));
                    }
                    event = subscription.recv() => {
                        let event = event?;
                        updates.modify(|snapshot| state.handle(event, snapshot));
                    }
                }
            }
        });
        Ok(Self {
            events,
            reports,
            facades,
            updates: receiver,
            worker,
        })
    }

    pub fn events(&self) -> HardwareEventBus {
        self.events.clone()
    }

    /// Where modules report their work; tests inject reports through it too.
    pub fn reports(&self) -> ModuleEventBus {
        self.reports.clone()
    }

    /// The public API of a registered module, such as
    /// `firmware.module::<Updates>()`.
    ///
    /// # Panics
    ///
    /// Panics if `F` is not a registered module, which startup rules out.
    #[expect(
        clippy::expect_used,
        reason = "startup builds every registered module, so a facade is always found"
    )]
    pub fn module<F: Facade>(&self) -> F {
        F::find(&self.facades).expect("startup builds every registered module")
    }

    pub fn snapshot(&self) -> Snapshot {
        self.updates.current()
    }

    /// Waits for a processed state newer than the supplied event count.
    ///
    /// # Errors
    ///
    /// Fails when the event loop stops first.
    pub async fn after(&mut self, processed_events: u64) -> io::Result<Snapshot> {
        self.until(|snapshot| snapshot.processed_events > processed_events)
            .await
    }

    /// Waits for a published state, including background results, that
    /// satisfies `condition`.
    ///
    /// # Errors
    ///
    /// Fails when the event loop stops first.
    pub async fn until(&mut self, condition: impl Fn(&Snapshot) -> bool) -> io::Result<Snapshot> {
        self.updates
            .wait_for(condition)
            .await
            .map_err(|_| io::Error::other("firmware event loop stopped before reaching the state"))
    }

    /// Runs until the application loop stops, reporting task failures and lag.
    ///
    /// # Errors
    ///
    /// Fails when the loop task panics or its subscriptions close or lag.
    pub async fn wait(&mut self) -> io::Result<()> {
        (&mut self.worker)
            .await
            .map_err(|error| io::Error::other(format!("firmware task failed: {error}")))?
            .map_err(io::Error::other)
    }

    /// Stops the loop and waits until it has released its resources.
    ///
    /// # Errors
    ///
    /// Fails when the loop had already failed.
    pub async fn shutdown(mut self) -> io::Result<()> {
        self.worker.abort();
        match (&mut self.worker).await {
            Err(error) if error.is_cancelled() => Ok(()),
            Err(error) => Err(io::Error::other(error)),
            Ok(result) => result.map_err(io::Error::other),
        }
    }
}

impl Drop for Firmware {
    fn drop(&mut self) {
        self.worker.abort();
    }
}
