use core::fmt::Debug;

use persistence::{KeyValueStore, LoadOutcome};

pub(crate) fn missing_values_are_unambiguous<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    let mut output = [0xAA; 4];

    assert_eq!(store.value_len(b"missing").expect("length succeeds"), None);
    assert!(!store.contains(b"missing").expect("contains succeeds"));
    assert_eq!(
        store.load(b"missing", &mut output).expect("load succeeds"),
        LoadOutcome::NotFound
    );
    assert_eq!(output, [0xAA; 4]);
}

pub(crate) fn binary_values_round_trip_and_overwrite<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    let key = [0, 0x80, 0xFF];
    let mut output = [0xAA; 6];

    store
        .store(&key, &[0, 0x7F, 0x80, 0xFF])
        .expect("binary value stores");
    assert_eq!(store.value_len(&key).expect("length succeeds"), Some(4));
    assert_eq!(
        store.load(&key, &mut output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 4 }
    );
    assert_eq!(&output[..4], &[0, 0x7F, 0x80, 0xFF]);
    assert_eq!(&output[4..], &[0xAA; 2]);

    store.store(&key, &[9, 8]).expect("value overwrites");
    assert_eq!(
        store.load(&key, &mut output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 2 }
    );
    assert_eq!(&output[..2], &[9, 8]);
}

pub(crate) fn undersized_buffers_are_never_partially_written<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    store
        .store(b"large", &[1, 2, 3, 4])
        .expect("fixture stores");
    let mut output = [0xAA; 3];

    assert_eq!(
        store.load(b"large", &mut output).expect("load succeeds"),
        LoadOutcome::BufferTooSmall { required: 4 }
    );
    assert_eq!(output, [0xAA; 3]);
}

pub(crate) fn empty_keys_and_values_remain_distinct_from_missing<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    let mut output = [];
    store.store(b"", b"").expect("empty entry stores");

    assert_eq!(store.value_len(b"").expect("length succeeds"), Some(0));
    assert_eq!(
        store.load(b"", &mut output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 0 }
    );
    assert_eq!(
        store.load(b"absent", &mut output).expect("load succeeds"),
        LoadOutcome::NotFound
    );
}

pub(crate) fn removal_and_flush_are_consistent<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    store.store(b"key", b"value").expect("value stores");
    store.flush().expect("writes flush");

    assert!(store.remove(b"key").expect("existing value removes"));
    assert!(!store.remove(b"key").expect("missing value does not remove"));
    assert!(!store.contains(b"key").expect("removed value is absent"));
    store.flush().expect("removal flushes");
}
