//! The application event loop, shared by the executable and E2E harness.

mod state;

use std::io;

use tokio::{runtime::Handle, sync::watch, task::JoinHandle};

use crate::{
    events::ReceiveError,
    hardware::HardwareEventBus,
    menu::transitions::{Config, TransitionEventBus, Transitions},
};
use state::State;

pub use state::Snapshot;

/// Owns one running firmware instance. Dropping it stops its event loop.
pub struct Firmware {
    events: HardwareEventBus,
    reports: TransitionEventBus,
    updates: watch::Receiver<Snapshot>,
    worker: JoinHandle<Result<(), ReceiveError>>,
}

impl Firmware {
    /// Starts the real application loop with no physical adapters attached.
    /// Hardware workers attach through `events()`; tests inject through it too.
    pub fn start() -> io::Result<Self> {
        Self::start_with(&Config::device())
    }

    /// Starts the loop with explicit integration settings. Stopping the loop
    /// cancels background work its transitions started.
    pub fn start_with(config: &Config) -> io::Result<Self> {
        let runtime = Handle::try_current().map_err(|error| {
            io::Error::other(format!(
                "starting firmware requires an async runtime: {error}"
            ))
        })?;
        let events = HardwareEventBus::new();
        // Subscribe before returning so even the first injected event is handled.
        let mut subscription = events.subscribe();
        let reports = TransitionEventBus::new();
        let mut reported = reports.subscribe();
        let mut state = State::new(Transitions::new(config, reports.clone()));
        let (updates, receiver) = watch::channel(state.initial_snapshot());
        let worker = runtime.spawn(async move {
            loop {
                tokio::select! {
                    // Results first, so a finished operation unblocks the menu
                    // before the next input is interpreted.
                    biased;
                    event = reported.recv() => {
                        let event = event?;
                        updates.send_modify(|snapshot| state.report(event, snapshot));
                    }
                    event = subscription.recv() => {
                        let event = event?;
                        updates.send_modify(|snapshot| state.handle(event, snapshot));
                    }
                }
            }
        });
        Ok(Self {
            events,
            reports,
            updates: receiver,
            worker,
        })
    }

    pub fn events(&self) -> HardwareEventBus {
        self.events.clone()
    }

    /// Where transitions report their work; tests inject reports through it too.
    pub fn reports(&self) -> TransitionEventBus {
        self.reports.clone()
    }

    pub fn snapshot(&self) -> Snapshot {
        self.updates.borrow().clone()
    }

    /// Waits for a processed state newer than the supplied event count.
    pub async fn after(&mut self, processed_events: u64) -> io::Result<Snapshot> {
        self.until(|snapshot| snapshot.processed_events > processed_events)
            .await
    }

    /// Waits for a published state, including background results, that
    /// satisfies `condition`.
    pub async fn until(&mut self, condition: impl Fn(&Snapshot) -> bool) -> io::Result<Snapshot> {
        loop {
            let snapshot = self.updates.borrow_and_update().clone();
            if condition(&snapshot) {
                return Ok(snapshot);
            }
            self.updates.changed().await.map_err(|_| {
                io::Error::other("firmware event loop stopped before reaching the state")
            })?;
        }
    }

    /// Runs until the application loop stops, reporting task failures and lag.
    pub async fn wait(&mut self) -> io::Result<()> {
        (&mut self.worker)
            .await
            .map_err(|error| io::Error::other(format!("firmware task failed: {error}")))?
            .map_err(io::Error::other)
    }

    /// Stops the loop and waits until it has released its resources.
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
