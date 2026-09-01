use std::{collections::BTreeMap, convert::Infallible};

use persistence::{KeyValueStore, LoadOutcome};

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub(crate) struct MemoryStore {
    entries: BTreeMap<Vec<u8>, Vec<u8>>,
}

impl MemoryStore {
    pub(crate) fn new() -> Self {
        Self::default()
    }

    pub(crate) fn len(&self) -> usize {
        self.entries.len()
    }

    pub(crate) fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub(crate) fn clear(&mut self) {
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
