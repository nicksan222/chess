use logger::{Level, Metadata, Record};

#[test]
fn metadata_and_record_expose_complete_context() {
    let metadata = Metadata::new(
        Level::Warn,
        "hardware",
        Some("firmware::board"),
        Some("src/board.rs"),
        Some(42),
    );
    let record = Record::new(metadata, format_args!("sensor changed"));

    assert_eq!(record.metadata(), &metadata);
    assert_eq!(record.level(), Level::Warn);
    assert_eq!(record.target(), "hardware");
    assert_eq!(record.module_path(), Some("firmware::board"));
    assert_eq!(record.file(), Some("src/board.rs"));
    assert_eq!(record.line(), Some(42));
    assert_eq!(record.arguments().to_string(), "sensor changed");
}

#[test]
fn manually_created_metadata_can_omit_source_location() {
    let metadata = Metadata::new(Level::Info, "remote", None, None, None);

    assert_eq!(metadata.module_path(), None);
    assert_eq!(metadata.file(), None);
    assert_eq!(metadata.line(), None);
}
