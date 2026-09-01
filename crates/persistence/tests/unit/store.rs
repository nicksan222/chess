use std::fmt::Debug;

use persistence::{KeyValueStore, LoadOutcome};

use crate::common::MemoryStore;

fn verify_store_contract<S>(store: &mut S)
where
    S: KeyValueStore,
    S::Error: Debug,
{
    let key = b"settings/brightness";
    let mut output = [0xAA; 8];

    assert_eq!(store.value_len(key).expect("length succeeds"), None);
    assert!(!store.contains(key).expect("contains succeeds"));
    assert_eq!(
        store.load(key, &mut output).expect("load succeeds"),
        LoadOutcome::NotFound
    );
    assert_eq!(output, [0xAA; 8]);
    assert!(!store.remove(key).expect("remove succeeds"));

    store.store(key, &[1, 2, 3, 4]).expect("store succeeds");
    assert_eq!(store.value_len(key).expect("length succeeds"), Some(4));
    assert!(store.contains(key).expect("contains succeeds"));

    let mut too_small = [0xCC; 3];
    assert_eq!(
        store.load(key, &mut too_small).expect("load succeeds"),
        LoadOutcome::BufferTooSmall { required: 4 }
    );
    assert_eq!(too_small, [0xCC; 3]);

    assert_eq!(
        store.load(key, &mut output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 4 }
    );
    assert_eq!(&output[..4], &[1, 2, 3, 4]);
    assert_eq!(&output[4..], &[0xAA; 4]);

    store.store(key, &[9, 8]).expect("overwrite succeeds");
    assert_eq!(store.value_len(key).expect("length succeeds"), Some(2));
    assert_eq!(
        store.load(key, &mut output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 2 }
    );
    assert_eq!(&output[..2], &[9, 8]);

    store.flush().expect("flush succeeds");
    assert!(store.remove(key).expect("remove succeeds"));
    assert!(!store.remove(key).expect("remove succeeds"));
}

#[test]
fn external_memory_store_satisfies_contract() {
    verify_store_contract(&mut MemoryStore::new());
}

#[test]
fn empty_keys_and_values_are_distinct_from_missing_entries() {
    let mut store = MemoryStore::new();
    let mut no_output = [];

    store.store(b"", b"").expect("store succeeds");

    assert_eq!(store.len(), 1);
    assert_eq!(store.value_len(b"").expect("length succeeds"), Some(0));
    assert_eq!(
        store.load(b"", &mut no_output).expect("load succeeds"),
        LoadOutcome::Loaded { len: 0 }
    );
    assert_eq!(
        store
            .load(b"missing", &mut no_output)
            .expect("load succeeds"),
        LoadOutcome::NotFound
    );
}

#[test]
fn mutable_references_forward_the_store_contract() {
    let mut store = MemoryStore::new();
    let mut reference = &mut store;

    verify_store_contract(&mut reference);
}

#[test]
fn test_backend_snapshots_are_independent() {
    let mut original = MemoryStore::new();
    original.store(b"one", b"1").expect("store succeeds");
    let mut snapshot = original.clone();

    original.remove(b"one").expect("remove succeeds");
    assert!(!original.contains(b"one").expect("contains succeeds"));
    assert!(snapshot.contains(b"one").expect("contains succeeds"));

    snapshot.clear();
    assert!(snapshot.is_empty());
    assert_eq!(original.len(), 0);
}

#[test]
fn load_outcome_reports_loaded_lengths_only() {
    assert_eq!(LoadOutcome::Loaded { len: 7 }.loaded_len(), Some(7));
    assert_eq!(LoadOutcome::NotFound.loaded_len(), None);
    assert_eq!(
        LoadOutcome::BufferTooSmall { required: 8 }.loaded_len(),
        None
    );
}
