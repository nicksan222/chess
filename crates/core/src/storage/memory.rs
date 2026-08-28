use alloc::{collections::BTreeMap, vec::Vec};
use core::convert::Infallible;

use super::{KeyValueStore, LoadOutcome};

/// An infallible, allocator-backed key/value store for tests and simulations.
///
/// Keys and values are owned byte sequences. Cloning a store produces an
/// independent snapshot.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct MemoryStore {
    entries: BTreeMap<Vec<u8>, Vec<u8>>,
}

impl MemoryStore {
    /// Creates an empty store without allocating.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            entries: BTreeMap::new(),
        }
    }

    /// Returns the number of stored keys.
    #[must_use]
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Returns whether no keys are stored.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Removes every key and value.
    pub fn clear(&mut self) {
        self.entries.clear();
    }
}

impl KeyValueStore for MemoryStore {
    type Error = Infallible;

    fn value_len(&mut self, key: &[u8]) -> Result<Option<usize>, Self::Error> {
        Ok(self.entries.get(key).map(Vec::len))
    }

    fn load(&mut self, key: &[u8], output: &mut [u8]) -> Result<LoadOutcome, Self::Error> {
        let Some(value) = self.entries.get(key) else {
            return Ok(LoadOutcome::NotFound);
        };

        if output.len() < value.len() {
            return Ok(LoadOutcome::BufferTooSmall {
                required: value.len(),
            });
        }

        output[..value.len()].copy_from_slice(value);
        Ok(LoadOutcome::Loaded { len: value.len() })
    }

    fn store(&mut self, key: &[u8], value: &[u8]) -> Result<(), Self::Error> {
        self.entries.insert(key.to_vec(), value.to_vec());
        Ok(())
    }

    fn remove(&mut self, key: &[u8]) -> Result<bool, Self::Error> {
        Ok(self.entries.remove(key).is_some())
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        Ok(())
    }
}
