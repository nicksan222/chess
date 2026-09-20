//! Hardware-free E2E entry point. There is no separate test event loop.

use std::{io, time::Duration};

use crate::{
    hardware::pins::ButtonEvent,
    runtime::{Firmware, Snapshot},
};

/// An isolated real firmware instance, with hardware replaced by event injection.
/// Events are injected sequentially so each returned snapshot acknowledges them.
pub struct FirmwareHarness {
    firmware: Firmware,
}

impl FirmwareHarness {
    pub fn start() -> io::Result<Self> {
        Ok(Self {
            firmware: Firmware::start()?,
        })
    }

    pub fn snapshot(&self) -> Snapshot {
        self.firmware.snapshot()
    }

    /// Injects a hardware observation and waits for the application to process
    /// it.
    pub async fn trigger(&mut self, event: ButtonEvent) -> io::Result<Snapshot> {
        let processed = self.snapshot().processed_events;
        self.firmware
            .events()
            .emit(event)
            .map_err(io::Error::other)?;
        tokio::time::timeout(Duration::from_secs(2), self.firmware.after(processed))
            .await
            .map_err(|_| {
                io::Error::new(
                    io::ErrorKind::TimedOut,
                    format!("firmware did not process {event:?}"),
                )
            })?
    }

    pub async fn shutdown(self) -> io::Result<()> {
        self.firmware.shutdown().await
    }
}
