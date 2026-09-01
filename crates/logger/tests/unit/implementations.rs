use logger::implementations::{StderrLogger, SystemdLogger};
use logger::{Level, LevelFilter, Logger, Metadata, Record};

fn metadata(level: Level) -> Metadata<'static> {
    Metadata::new(level, "firmware", None, None, None)
}

#[test]
fn stderr_logger_filters_at_its_configured_level() {
    let logger = StderrLogger::new(LevelFilter::Debug);

    assert_eq!(logger.max_level(), LevelFilter::Debug);
    assert!(logger.enabled(&metadata(Level::Error)));
    assert!(logger.enabled(&metadata(Level::Debug)));
    assert!(!logger.enabled(&metadata(Level::Trace)));
}

#[test]
fn systemd_logger_filters_at_its_configured_level() {
    let logger = SystemdLogger::new(LevelFilter::Warn);

    assert_eq!(logger.max_level(), LevelFilter::Warn);
    assert!(logger.enabled(&metadata(Level::Error)));
    assert!(logger.enabled(&metadata(Level::Warn)));
    assert!(!logger.enabled(&metadata(Level::Info)));
}

#[test]
fn hosted_loggers_default_to_info() {
    assert_eq!(StderrLogger::default().max_level(), LevelFilter::Info);
    assert_eq!(SystemdLogger::default().max_level(), LevelFilter::Info);
}

#[test]
fn hosted_loggers_accept_records_through_the_shared_trait() {
    fn send_ready_record(logger: &dyn Logger) {
        logger.log(Record::new(metadata(Level::Info), format_args!("ready")));
        logger.flush();
    }

    send_ready_record(&StderrLogger::default());
    send_ready_record(&SystemdLogger::default());
}
