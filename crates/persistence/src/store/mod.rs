mod outcome;

pub use outcome::LoadOutcome;

/// A synchronous key/value persistence backend supplied by the application.
///
/// This trait deliberately does not prescribe serialization, allocation,
/// transactions, or database queries. Implementations may represent embedded
/// flash, files, SQLite rows, remote services, or test doubles. Methods take
/// `&mut self` so stateful drivers need no interior mutability.
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

impl<S> KeyValueStore for &mut S
where
    S: KeyValueStore + ?Sized,
{
    type Error = S::Error;

    fn value_len(&mut self, key: &[u8]) -> Result<Option<usize>, Self::Error> {
        (**self).value_len(key)
    }

    fn load(&mut self, key: &[u8], output: &mut [u8]) -> Result<LoadOutcome, Self::Error> {
        (**self).load(key, output)
    }

    fn store(&mut self, key: &[u8], value: &[u8]) -> Result<(), Self::Error> {
        (**self).store(key, value)
    }

    fn remove(&mut self, key: &[u8]) -> Result<bool, Self::Error> {
        (**self).remove(key)
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        (**self).flush()
    }
}
