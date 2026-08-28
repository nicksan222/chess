//! Narrow persistence capabilities and reusable test backends.
//!
//! Domain-specific repositories should own serialization, keys, migrations,
//! and persistence policy. This module only defines byte-storage mechanics.

mod memory;

pub use memory::MemoryStore;

/// The result of loading a value into caller-provided storage.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[must_use]
pub enum LoadOutcome {
    /// The key does not exist.
    NotFound,

    /// The complete value was copied into the beginning of the output buffer.
    Loaded {
        /// The number of bytes copied. This may be zero for an empty value.
        len: usize,
    },

    /// The value exists, but the output buffer is too small.
    ///
    /// Implementations must leave the output buffer unchanged in this case.
    BufferTooSmall {
        /// The minimum output length required to load the complete value.
        required: usize,
    },
}

impl LoadOutcome {
    /// Returns the loaded byte count, or `None` if no value was loaded.
    #[must_use]
    pub const fn loaded_len(self) -> Option<usize> {
        match self {
            Self::Loaded { len } => Some(len),
            Self::NotFound | Self::BufferTooSmall { .. } => None,
        }
    }
}

/// Synchronous key/value byte storage.
///
/// This trait deliberately does not prescribe serialization, allocation,
/// transactions, or database queries. Implementations may represent RAM,
/// files, SQLite rows, or embedded flash. Methods take `&mut self` so adapters
/// for stateful hardware drivers do not require interior mutability.
///
/// A successful method call has completed from the caller's perspective, but
/// durability and power-loss atomicity remain implementation-specific. Call
/// [`KeyValueStore::flush`] when a durability boundary is required.
pub trait KeyValueStore {
    /// Backend-specific failures.
    type Error;

    /// Returns the stored value length, or `None` when `key` is absent.
    fn value_len(&mut self, key: &[u8]) -> Result<Option<usize>, Self::Error>;

    /// Loads the complete value for `key` into `output`.
    ///
    /// Implementations must not partially copy a value. When `output` is too
    /// small, they return [`LoadOutcome::BufferTooSmall`] and leave it unchanged.
    fn load(&mut self, key: &[u8], output: &mut [u8]) -> Result<LoadOutcome, Self::Error>;

    /// Stores `value` under `key`, replacing any previous value.
    fn store(&mut self, key: &[u8], value: &[u8]) -> Result<(), Self::Error>;

    /// Removes `key`, returning whether a value existed.
    fn remove(&mut self, key: &[u8]) -> Result<bool, Self::Error>;

    /// Makes successful writes durable to the extent supported by the backend.
    fn flush(&mut self) -> Result<(), Self::Error>;

    /// Returns whether `key` exists.
    fn contains(&mut self, key: &[u8]) -> Result<bool, Self::Error> {
        self.value_len(key).map(|len| len.is_some())
    }
}
