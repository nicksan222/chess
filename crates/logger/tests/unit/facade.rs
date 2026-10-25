use std::sync::{
    Mutex,
    atomic::{AtomicU8, AtomicUsize, Ordering},
};

use logger::{
    Level, LevelFilter, Logger, Metadata, NopLogger, Record, debug, error, flush, get, info, log,
    register, trace, warn,
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
    max_level: AtomicU8,
    records: Mutex<Vec<Captured>>,
    flushes: AtomicUsize,
}

impl CaptureLogger {
    const fn new() -> Self {
        Self {
            max_level: AtomicU8::new(LevelFilter::Trace as u8),
            records: Mutex::new(Vec::new()),
            flushes: AtomicUsize::new(0),
        }
    }

    fn set_max_level(&self, level: LevelFilter) {
        self.max_level.store(level as u8, Ordering::Relaxed);
    }

    fn take(&self) -> Vec<Captured> {
        std::mem::take(&mut *self.records.lock().unwrap())
    }
}

impl Logger for CaptureLogger {
    fn enabled(&self, metadata: &Metadata<'_>) -> bool {
        metadata.level() as u8 <= self.max_level.load(Ordering::Relaxed)
    }

    fn log(&self, record: Record<'_>) {
        self.records.lock().unwrap().push(Captured {
            level: record.level(),
            target: record.target().to_owned(),
            module_path: record.module_path().map(str::to_owned),
            file: record.file().map(str::to_owned),
            line: record.line(),
            message: record.arguments().to_string(),
        });
    }

    fn flush(&self) {
        self.flushes.fetch_add(1, Ordering::Relaxed);
    }
}

struct OtherLogger;

impl Logger for OtherLogger {
    fn log(&self, _record: Record<'_>) {}
}

static CAPTURE: CaptureLogger = CaptureLogger::new();
static OTHER: OtherLogger = OtherLogger;

#[test]
fn registered_logger_is_the_single_logging_path() {
    assert_registration_is_permanent();
    let records = assert_level_macros_reach_the_logger();
    assert_macros_record_source_location(&records);
    assert_target_and_source_location();
    assert_filtering_skips_argument_evaluation();
    assert_flush_and_nop_logger();
}

fn assert_registration_is_permanent() {
    assert!(get().is_none());
    register(&CAPTURE).unwrap();
    assert!(core::ptr::eq(get().unwrap(), &CAPTURE));
    assert_eq!(register(&CAPTURE), Ok(()));
    assert!(register(&OTHER).is_err());
}

fn emit_one_record_per_level() {
    error!("error");
    warn!("warn");
    info!("info");
    debug!("debug");
    trace!("trace");
    log!(level: Level::Info, "manual");
}

fn levels(records: &[Captured]) -> Vec<Level> {
    records.iter().map(|record| record.level).collect()
}

fn assert_level_macros_reach_the_logger() -> Vec<Captured> {
    emit_one_record_per_level();

    let records = CAPTURE.take();
    assert_eq!(
        levels(&records),
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
    records
}

fn assert_macros_record_source_location(records: &[Captured]) {
    assert!(records.iter().all(|record| record.module_path.is_some()));
    assert!(records.iter().all(|record| record.file.is_some()));
    assert!(records.iter().all(|record| record.line.is_some()));
}

fn assert_target_and_source_location() {
    let source_line = line!() + 1;
    info!(target: "board::sensors", "square {} is occupied", 12);
    assert_eq!(
        CAPTURE.take(),
        [Captured {
            level: Level::Info,
            target: "board::sensors".to_owned(),
            module_path: Some(module_path!().to_owned()),
            file: Some(file!().to_owned()),
            line: Some(source_line),
            message: "square 12 is occupied".to_owned(),
        }]
    );
}

fn assert_filtering_skips_argument_evaluation() {
    CAPTURE.set_max_level(LevelFilter::Warn);
    let evaluations = AtomicUsize::new(0);
    debug!("unused {}", evaluations.fetch_add(1, Ordering::Relaxed));
    assert_eq!(evaluations.load(Ordering::Relaxed), 0);
    assert_eq!(CAPTURE.take(), Vec::new());
}

fn assert_flush_and_nop_logger() {
    flush();
    assert_eq!(CAPTURE.flushes.load(Ordering::Relaxed), 1);

    let nop = NopLogger;
    let metadata = Metadata::new(Level::Error, "test");
    assert!(!nop.enabled(&metadata));
    nop.log(Record::new(metadata, format_args!("discarded")));
}
