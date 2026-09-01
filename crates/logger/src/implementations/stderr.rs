use std::io::{self, Write};

use crate::{LevelFilter, Logger, Metadata, Record};

/// Human-readable logger for terminals, desktop applications, and simulators.
///
/// Each enabled record is written to standard error as one line.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct StderrLogger {
    max_level: LevelFilter,
}

impl StderrLogger {
    /// Creates a stderr logger with the supplied maximum verbosity.
    pub const fn new(max_level: LevelFilter) -> Self {
        Self { max_level }
    }

    /// Returns the maximum enabled verbosity.
    pub const fn max_level(&self) -> LevelFilter {
        self.max_level
    }
}

impl Default for StderrLogger {
    fn default() -> Self {
        Self::new(LevelFilter::Info)
    }
}

impl Logger for StderrLogger {
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        self.max_level.allows(metadata.level())
    }

    fn log(&self, record: Record<'_>) {
        let mut stderr = io::stderr().lock();

        match (record.file(), record.line()) {
            (Some(file), Some(line)) => {
                let _ = writeln!(
                    stderr,
                    "[{} {}] {} ({file}:{line})",
                    record.level(),
                    record.target(),
                    record.arguments()
                );
            }
            _ => {
                let _ = writeln!(
                    stderr,
                    "[{} {}] {}",
                    record.level(),
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
