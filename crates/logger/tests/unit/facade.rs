use std::cell::{Cell, RefCell};

use logger::{
    Level, LevelFilter, Logger, Metadata, NopLogger, Record, debug, error, info, log, trace, warn,
};

#[derive(Debug, Eq, PartialEq)]
struct Captured {
    level: Level,
    target: String,
    module_path: Option<String>,
    file: Option<String>,
    line: Option<u32>,
    message: String,
}

struct CaptureLogger {
    filter: LevelFilter,
    records: RefCell<Vec<Captured>>,
    flushes: Cell<usize>,
}

impl CaptureLogger {
    fn new(filter: LevelFilter) -> Self {
        Self {
            filter,
            records: RefCell::new(Vec::new()),
            flushes: Cell::new(0),
        }
    }
}

impl Logger for CaptureLogger {
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        self.filter.allows(metadata.level())
    }

    fn log(&self, record: Record<'_>) {
        self.records.borrow_mut().push(Captured {
            level: record.level(),
            target: record.target().to_owned(),
            module_path: record.module_path().map(str::to_owned),
            file: record.file().map(str::to_owned),
            line: record.line(),
            message: record.arguments().to_string(),
        });
    }

    fn flush(&self) {
        self.flushes.set(self.flushes.get() + 1);
    }
}

#[test]
fn every_macro_emits_its_level() {
    let logger = CaptureLogger::new(LevelFilter::Trace);

    error!(logger, "error");
    warn!(logger, "warn");
    info!(logger, "info");
    debug!(logger, "debug");
    trace!(logger, "trace");
    log!(logger, Level::Info, "manual");

    let records = logger.records.borrow();
    let levels: Vec<_> = records.iter().map(|record| record.level).collect();
    assert_eq!(
        levels,
        [
            Level::Error,
            Level::Warn,
            Level::Info,
            Level::Debug,
            Level::Trace,
            Level::Info,
        ]
    );
    assert_eq!(records[0].target, module_path!());
    assert_eq!(records[5].message, "manual");
    assert!(records.iter().all(|record| record.module_path.is_some()));
    assert!(records.iter().all(|record| record.file.is_some()));
    assert!(records.iter().all(|record| record.line.is_some()));
}

#[test]
fn custom_targets_and_formatting_reach_the_backend() {
    let logger = CaptureLogger::new(LevelFilter::Info);

    info!(logger, target: "board::sensors", "square {} is {}", 12, "occupied");

    let records = logger.records.borrow();
    assert_eq!(records[0].target, "board::sensors");
    assert_eq!(records[0].message, "square 12 is occupied");
}

#[test]
fn disabled_records_do_not_evaluate_message_arguments() {
    let logger = CaptureLogger::new(LevelFilter::Warn);
    let evaluations = Cell::new(0);
    let value = || {
        evaluations.set(evaluations.get() + 1);
        7
    };

    debug!(logger, "unused {}", value());

    assert_eq!(evaluations.get(), 0);
    assert!(logger.records.borrow().is_empty());
}

#[test]
fn references_forward_all_logger_operations() {
    let logger = CaptureLogger::new(LevelFilter::Info);
    let reference: &dyn Logger = &logger;

    info!(reference, "through trait object");
    reference.flush();

    assert_eq!(logger.records.borrow().len(), 1);
    assert_eq!(logger.flushes.get(), 1);
}

#[test]
fn nop_logger_rejects_and_discards_records() {
    let logger = NopLogger;
    let metadata = Metadata::new(Level::Error, "test", None, None, None);

    assert!(!logger.enabled(&metadata));
    error!(logger, "discarded");
    logger.flush();
}
