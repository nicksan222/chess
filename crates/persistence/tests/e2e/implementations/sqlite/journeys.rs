use chess_core::{Percentage, Toggle};
use persistence::{KeyValueStore, implementations::SqliteStore, retrieve, save};

use super::support::{DatabaseFile, Settings};

#[test]
fn settings_survive_a_complete_sqlite_reopen_journey() {
    let database = DatabaseFile::new("reopen");
    let fields = Settings::new();

    {
        let mut store = SqliteStore::open(database.path()).expect("database opens");

        assert_eq!(
            retrieve!(&mut store, fields.sound).expect("missing field is readable"),
            None
        );
        save!(&mut store, fields.sound, Toggle::On).expect("sound saves");
        save!(
            &mut store,
            fields.brightness,
            Percentage::new(65).expect("valid percentage"),
        )
        .expect("brightness saves");
        save!(&mut store, fields.launches, 1_u32).expect("launch count saves");
        save!(
            &mut store,
            fields.device_id,
            [0x10, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE],
        )
        .expect("device identity saves");

        save!(&mut store, fields.launches, 2_u32).expect("launch count overwrites");
        store.flush().expect("committed writes flush");
    }

    let mut reopened = SqliteStore::open(database.path()).expect("database reopens");
    assert_eq!(
        retrieve!(&mut reopened, fields.sound).expect("sound retrieves"),
        Some(Toggle::On)
    );
    assert_eq!(
        retrieve!(&mut reopened, fields.brightness).expect("brightness retrieves"),
        Percentage::new(65).ok()
    );
    assert_eq!(
        retrieve!(&mut reopened, fields.launches).expect("launch count retrieves"),
        Some(2)
    );
    assert_eq!(
        retrieve!(&mut reopened, fields.device_id).expect("device identity retrieves"),
        Some([0x10, 0x32, 0x54, 0x76, 0x98, 0xBA, 0xDC, 0xFE])
    );

    assert!(
        reopened
            .remove(fields.sound.key())
            .expect("existing field removes")
    );
    assert!(
        !reopened
            .remove(fields.sound.key())
            .expect("missing field remains harmless")
    );
    assert_eq!(
        retrieve!(&mut reopened, fields.sound).expect("removed field retrieves"),
        None
    );
}

#[test]
fn sqlite_preserves_empty_and_non_utf8_binary_data() {
    let mut store = SqliteStore::in_memory().expect("in-memory database opens");
    let key = [0, 0x80, 0xFF];
    let value = [0, 0x7F, 0x80, 0xFF];
    let mut output = [0; 4];

    store.store(&key, &value).expect("binary value stores");
    assert_eq!(store.value_len(&key).expect("length reads"), Some(4));
    assert_eq!(
        store.load(&key, &mut output).expect("binary value loads"),
        persistence::LoadOutcome::Loaded { len: 4 }
    );
    assert_eq!(output, value);

    store.store(b"", b"").expect("empty value stores");
    assert_eq!(store.value_len(b"").expect("empty length reads"), Some(0));
    assert!(store.contains(b"").expect("empty key exists"));
}

#[test]
fn consumer_controlled_sqlite_transactions_can_roll_back() {
    let fields = Settings::new();
    let mut store = SqliteStore::in_memory().expect("in-memory database opens");

    store
        .connection_mut()
        .execute_batch("BEGIN")
        .expect("transaction starts");
    save!(&mut store, fields.launches, 9_u32).expect("transactional value writes");
    store
        .connection_mut()
        .execute_batch("ROLLBACK")
        .expect("transaction rolls back");

    assert_eq!(
        retrieve!(&mut store, fields.launches).expect("rolled-back field reads"),
        None
    );
}
