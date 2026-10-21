//! Hardware-free E2E entry point. There is no separate test event loop.

use std::{io, time::Duration};

use crate::{
    hardware::HardwareEvent,
    runtime::{Config, Firmware, Snapshot, TransitionEvent},
};

/// An isolated real firmware instance, with hardware replaced by event injection.
/// Events are injected sequentially so each returned snapshot acknowledges them.
pub struct FirmwareHarness {
    firmware: Firmware,
}

impl FirmwareHarness {
    /// Starts firmware with [`Config::offline`], so tests never reach the network.
    pub fn start() -> io::Result<Self> {
        Self::with_config(&Config::offline())
    }

    /// Starts firmware with explicit integration settings, such as a local fake.
    pub fn with_config(config: &Config) -> io::Result<Self> {
        Ok(Self {
            firmware: Firmware::start_with(config)?,
        })
    }

    pub fn snapshot(&self) -> Snapshot {
        self.firmware.snapshot()
    }

    /// Injects a hardware observation and waits for the application to process
    /// it.
    pub async fn trigger<E>(&mut self, event: E) -> io::Result<Snapshot>
    where
        E: Into<HardwareEvent>,
    {
        let event = event.into();
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

    /// Injects a transition report, as background work would send it, and waits
    /// for the application to apply it. Acknowledgement counts reports, so no
    /// real background report may be in flight.
    pub async fn report(&mut self, event: TransitionEvent) -> io::Result<Snapshot> {
        let reported = self.snapshot().reported_events;
        self.firmware
            .reports()
            .emit(event)
            .map_err(io::Error::other)?;
        self.until(|snapshot| snapshot.reported_events > reported)
            .await
    }

    /// Waits for background work, such as an update check, to reach a state.
    pub async fn until(&mut self, condition: impl Fn(&Snapshot) -> bool) -> io::Result<Snapshot> {
        tokio::time::timeout(Duration::from_secs(5), self.firmware.until(condition))
            .await
            .map_err(|_| {
                io::Error::new(
                    io::ErrorKind::TimedOut,
                    format!(
                        "firmware never reached the state; last {:?}",
                        self.snapshot()
                    ),
                )
            })?
    }

    pub async fn shutdown(self) -> io::Result<()> {
        self.firmware.shutdown().await
    }
}

#[cfg(test)]
mod tests {
    use super::FirmwareHarness;

    #[test]
    fn starting_firmware_without_runtime_is_an_error() {
        assert!(FirmwareHarness::start().is_err());
    }
}
