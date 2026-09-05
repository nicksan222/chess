//! The application event loop, shared by the executable and E2E harness.

mod state;

use std::io;

use tokio::{runtime::Handle, sync::watch, task::JoinHandle};

use crate::events::{EventEmitter, ReceiveError};
use state::State;

pub use state::Snapshot;

/// Owns one running firmware instance. Dropping it stops its event loop.
pub struct Firmware {
    events: EventEmitter,
    updates: watch::Receiver<Snapshot>,
    worker: JoinHandle<Result<(), ReceiveError>>,
}

impl Firmware {
    /// Starts the real application loop with no physical adapters attached.
    /// Hardware workers attach through `events()`; tests inject through it too.
    pub fn start() -> io::Result<Self> {
        let runtime = Handle::try_current().map_err(|error| {
            io::Error::other(format!(
                "starting firmware requires an async runtime: {error}"
            ))
        })?;
        let events = EventEmitter::new();
        // Subscribe before returning so even the first injected event is handled.
        let mut subscription = events.subscribe();
        let mut state = State::new();
        let (updates, receiver) = watch::channel(state.snapshot());
        let worker = runtime.spawn(async move {
            loop {
                let event = subscription.recv().await?;
                state.handle(event);
                updates.send_replace(state.snapshot());
            }
        });
        Ok(Self {
            events,
            updates: receiver,
            worker,
        })
    }

    pub fn events(&self) -> EventEmitter {
        self.events.clone()
    }

    pub fn snapshot(&self) -> Snapshot {
        self.updates.borrow().clone()
    }

    /// Waits for a processed state newer than the supplied event count.
    pub async fn after(&mut self, processed_events: u64) -> io::Result<Snapshot> {
        loop {
            let snapshot = self.updates.borrow_and_update().clone();
            if snapshot.processed_events > processed_events {
                return Ok(snapshot);
            }
            self.updates.changed().await.map_err(|_| {
                io::Error::other("firmware event loop stopped before processing the event")
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
