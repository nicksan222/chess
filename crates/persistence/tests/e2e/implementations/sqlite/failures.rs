use std::fs;

use chess_core::{Percentage, Toggle};
use persistence::{
    KeyValueStore, RetrieveError, SaveError, ValueDecodeError, implementations::SqliteStore,
    retrieve, save,
};

use super::support::{DatabaseFile, Settings};

#[test]
fn malformed_database_files_fail_during_open() {
    let database = DatabaseFile::new("malformed");
    fs::write(database.path(), b"this is not a sqlite database").expect("malformed fixture writes");

    let error = match SqliteStore::open(database.path()) {
        Ok(_) => panic!("malformed database must not open"),
        Err(error) => error,
    };
    assert!(
        error.to_string().contains("database") || error.to_string().contains("file"),
        "unexpected SQLite error: {error}"
    );
}

#[test]
fn corrupt_stored_values_return_typed_decode_errors() {
    let fields = Settings::new();
    let mut store = SqliteStore::in_memory().expect("in-memory database opens");

    store
        .store(fields.sound.key(), &[2])
        .expect("corrupt fixture stores");
    assert!(matches!(
        retrieve!(&mut store, fields.sound),
        Err(RetrieveError::Decode(
            ValueDecodeError::InvalidDiscriminant { value: 2 }
        ))
    ));

    store
        .store(fields.brightness.key(), &[101])
        .expect("out-of-range fixture stores");
    assert!(matches!(
        retrieve!(&mut store, fields.brightness),
        Err(RetrieveError::Decode(ValueDecodeError::OutOfRange {
            value: 101,
            maximum: 100,
        }))
    ));

    // A valid value still round-trips after independent corrupt fields fail.
    save!(&mut store, fields.sound, Toggle::Off).expect("replacement saves");
    save!(
        &mut store,
        fields.brightness,
        Percentage::new(100).expect("valid percentage"),
    )
    .expect("replacement saves");
}

#[test]
fn undersized_load_buffers_are_reported_without_partial_writes() {
    let fields = Settings::new();
    let mut store = SqliteStore::in_memory().expect("in-memory database opens");
    save!(&mut store, fields.launches, 0x0102_0304_u32).expect("counter saves");
    let mut scratch = [0xAA; 3];

    assert!(matches!(
        fields.launches.retrieve(&mut store, &mut scratch),
        Err(RetrieveError::BufferTooSmall {
            required: 4,
            available: 3,
        })
    ));
    assert_eq!(scratch, [0xAA; 3]);
}

#[test]
fn sqlite_failures_remain_distinct_from_codec_failures() {
    let fields = Settings::new();
    let mut store = SqliteStore::in_memory().expect("in-memory database opens");
    store
        .connection_mut()
        .execute_batch("DROP TABLE persistence_values")
        .expect("failure fixture drops backing table");

    assert!(matches!(
        retrieve!(&mut store, fields.sound),
        Err(RetrieveError::Backend(_))
    ));
    assert!(matches!(
        save!(&mut store, fields.sound, Toggle::On),
        Err(SaveError::Backend(_))
    ));
    assert!(store.flush().is_ok(), "flush has no pending SQLite work");
}
