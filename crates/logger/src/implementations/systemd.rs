use std::io::{self, Write};

use crate::{Level, LevelFilter, Logger, Metadata, Record};

/// Logger for the systemd-supervised Yocto firmware.
///
/// Records go to standard error. systemd captures that stream in its journal.
/// The number at the beginning tells systemd how severe the record is.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SystemdLogger {
    max_level: LevelFilter,
}

impl SystemdLogger {
    /// Creates a systemd logger with the supplied maximum verbosity.
    pub const fn new(max_level: LevelFilter) -> Self {
        Self { max_level }
    }

    /// Returns the maximum enabled verbosity.
    pub const fn max_level(&self) -> LevelFilter {
        self.max_level
    }
}

impl Default for SystemdLogger {
    fn default() -> Self {
        Self::new(LevelFilter::Info)
    }
}

impl Logger for SystemdLogger {
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        self.max_level.allows(metadata.level())
    }

    fn log(&self, record: Record<'_>) {
        let mut stderr = io::stderr().lock();
        let priority = systemd_priority(record.level());

        match (record.file(), record.line()) {
            (Some(file), Some(line)) => {
                let _ = writeln!(
                    stderr,
                    "<{priority}>{}: {} ({file}:{line})",
                    record.target(),
                    record.arguments()
                );
            }
            _ => {
                let _ = writeln!(
                    stderr,
                    "<{priority}>{}: {}",
                    record.target(),
                    record.arguments()
                );
            }
        }
    }

    fn flush(&self) {
        let _ = io::stderr().flush();
    }
}

const fn systemd_priority(level: Level) -> u8 {
    match level {
        Level::Error => 3,
        Level::Warn => 4,
        Level::Info => 6,
        Level::Debug | Level::Trace => 7,
    }
}
