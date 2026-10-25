//! Polls the eight TCA9554 Hall-sensor banks and publishes piece changes.
//!
//! The board has no sensor interrupt: every scan interval the poller reads
//! banks 0x20–0x27 in order, keeps a change only once enough complete scans
//! agree (both set by [`HallTuning`]), and emits [`PieceEvent`](super::PieceEvent)s on the
//! hardware bus. The first stable scan reports every occupied square as placed,
//! so subscribers learn the starting position from the same stream. A failed
//! bank reports nothing until it is reconfigured and its squares reconciled.

mod bank;
mod change;
#[cfg(test)]
mod fake;
mod filter;
mod monitor;
mod scanner;
mod tca9554;

use std::{
    io,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};

use embedded_hal::i2c::I2c;
use tokio::{runtime::Handle, task::JoinHandle};

use super::HardwareEventBus;
use crate::tuning::HallTuning;
use scanner::Scanner;

pub use bank::{FIRST_ADDRESS, HallBank};

/// A running Hall poller. Dropping it stops publication and further scans.
/// An in-flight kernel transfer finishes before its bus can be released.
pub struct HallSensors {
    worker: JoinHandle<()>,
    stopped: Arc<AtomicBool>,
}

impl HallSensors {
    /// Polls the banks on a Linux I2C character device such as `/dev/i2c-1`.
    /// Failing to open the device fails startup; an unresponsive bank does not.
    #[cfg(target_os = "linux")]
    pub fn open(
        bus: impl AsRef<std::path::Path>,
        events: &HardwareEventBus,
        tuning: HallTuning,
    ) -> io::Result<Self> {
        let bus = bus.as_ref();
        let i2c = super::linux_i2c::LinuxI2c::open(bus).map_err(|cause| {
            let error = io::Error::new(
                cause.kind(),
                format!("opening Hall sensor bus {}: {cause}", bus.display()),
            );
            logger::error!("{error}; firmware startup cannot continue");
            error
        })?;
        let sensors = Self::start(i2c, events, tuning)?;
        logger::info!(
            "Hall sensors polling {} banks on {} every {} ms, reporting after {} agreeing scans",
            HallBank::COUNT,
            bus.display(),
            tuning.scan_interval.as_millis(),
            tuning.stable_scans
        );
        Ok(sensors)
    }

    /// Starts the same poller with an injected bus.
    pub fn start<I>(mut i2c: I, events: &HardwareEventBus, tuning: HallTuning) -> io::Result<Self>
    where
        I: I2c + Send + 'static,
    {
        let runtime = Handle::try_current()
            .map_err(|_| io::Error::other("Hall sensors require an active Tokio runtime"))?;
        if tuning.scan_interval.is_zero() || tuning.stable_scans == 0 {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "Hall scan interval and stability count must be positive",
            ));
        }
        let events = events.clone();
        let stopped = Arc::new(AtomicBool::new(false));
        let cancelled = Arc::clone(&stopped);
        let worker = runtime.spawn(async move {
            let mut interval = tokio::time::interval(tuning.scan_interval);
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            let mut scanner = Scanner::new(tuning);
            loop {
                interval.tick().await;
                // A kernel I2C transfer can wait for a bus timeout. Keep it off
                // the single-thread application loop, with only one scan in flight.
                let stop = Arc::clone(&cancelled);
                let scan = tokio::task::spawn_blocking(move || {
                    let changes = scanner.scan_while(&mut i2c, || !stop.load(Ordering::Acquire));
                    (scanner, i2c, changes)
                })
                .await;
                let changes;
                (scanner, i2c, changes) = match scan {
                    Ok(result) => result,
                    Err(error) => {
                        logger::error!("Hall acquisition worker failed: {error}");
                        break;
                    }
                };
                for event in changes {
                    let _ = events.emit(event.into());
                }
            }
        });
        Ok(Self { worker, stopped })
    }
}

impl Drop for HallSensors {
    fn drop(&mut self) {
        self.stopped.store(true, Ordering::Release);
        self.worker.abort();
    }
}
