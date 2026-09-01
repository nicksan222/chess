use logger::{Level, LevelFilter};

#[test]
fn levels_are_ordered_by_verbosity() {
    assert!(Level::Error < Level::Warn);
    assert!(Level::Warn < Level::Info);
    assert!(Level::Info < Level::Debug);
    assert!(Level::Debug < Level::Trace);
}

#[test]
fn filters_accept_their_level_and_every_more_severe_level() {
    assert!(!LevelFilter::Off.allows(Level::Error));
    assert!(LevelFilter::Warn.allows(Level::Error));
    assert!(LevelFilter::Warn.allows(Level::Warn));
    assert!(!LevelFilter::Warn.allows(Level::Info));
    assert!(LevelFilter::Trace.allows(Level::Trace));
}

#[test]
fn levels_have_stable_display_names_and_filter_conversion() {
    assert_eq!(Level::Debug.to_string(), "DEBUG");
    assert_eq!(LevelFilter::Off.to_string(), "OFF");
    assert_eq!(LevelFilter::from(Level::Info), LevelFilter::Info);
    assert_eq!(LevelFilter::default(), LevelFilter::Off);
}
