use core::{fmt, marker::PhantomData};

use crate::{
    DecodeValue, EncodeValue, InlineValue, KeyValueStore, LoadOutcome, RetrieveError, SaveError,
};

/// A stable storage key associated with exactly one Rust value type.
///
/// Fields are zero-allocation descriptors. They contain no value and may be
/// shared freely; a schema groups them so consumers have one explicit inventory
/// of everything their application persists.
///
/// A field's declared type is preserved through retrieval:
///
/// ```compile_fail
/// use chess_core::{Percentage, Toggle};
/// use persistence::{KeyValueStore, persistence_schema};
///
/// persistence_schema! {
///     struct Settings {
///         sound: Toggle = b"sound",
///     }
/// }
///
/// fn wrong_type<S: KeyValueStore>(store: &mut S, scratch: &mut [u8]) {
///     let fields = Settings::new();
///     let _: Result<Option<Percentage>, _> = fields.sound.retrieve(store, scratch);
/// }
/// ```
pub struct Field<T> {
    key: &'static [u8],
    value: PhantomData<fn() -> T>,
}

impl<T> Clone for Field<T> {
    fn clone(&self) -> Self {
        *self
    }
}

impl<T> Copy for Field<T> {}

impl<T> fmt::Debug for Field<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Field")
            .field("key", &self.key)
            .field("value_type", &core::any::type_name::<T>())
            .finish()
    }
}

impl<T> PartialEq for Field<T> {
    fn eq(&self, other: &Self) -> bool {
        self.key == other.key
    }
}

impl<T> Eq for Field<T> {}

impl<T> Field<T> {
    /// Associates `key` with `T`.
    ///
    /// Prefer [`persistence_schema!`](crate::persistence_schema), which keeps
    /// every field in one consumer-defined schema.
    #[must_use]
    pub const fn new(key: &'static [u8]) -> Self {
        Self {
            key,
            value: PhantomData,
        }
    }

    /// Returns this field's stable backend key.
    #[must_use]
    pub const fn key(&self) -> &'static [u8] {
        self.key
    }
}

impl<T> Field<T>
where
    T: EncodeValue,
{
    /// Encodes and stores `value` under this field's key.
    ///
    /// The backend is not called when encoding fails. Bytes beyond the encoded
    /// prefix of `scratch` are never stored.
    pub fn save<S>(
        &self,
        store: &mut S,
        value: &T,
        scratch: &mut [u8],
    ) -> Result<(), SaveError<S::Error, T::Error>>
    where
        S: KeyValueStore + ?Sized,
    {
        let written = value.encode_value(scratch).map_err(SaveError::Encode)?;
        if written > scratch.len() {
            return Err(SaveError::InvalidEncodedLength {
                reported: written,
                capacity: scratch.len(),
            });
        }
        store
            .store(self.key, &scratch[..written])
            .map_err(SaveError::Backend)
    }
}

impl<T> Field<T>
where
    T: InlineValue,
{
    /// Saves an inline value without requiring a caller-provided buffer.
    pub fn save_inline<S>(
        &self,
        store: &mut S,
        value: &T,
    ) -> Result<(), SaveError<S::Error, <T as EncodeValue>::Error>>
    where
        S: KeyValueStore + ?Sized,
    {
        let mut scratch = T::Buffer::default();
        self.save(store, value, scratch.as_mut())
    }

    /// Retrieves an inline value without requiring a caller-provided buffer.
    pub fn retrieve_inline<S>(
        &self,
        store: &mut S,
    ) -> Result<Option<T>, RetrieveError<S::Error, <T as DecodeValue>::Error>>
    where
        S: KeyValueStore + ?Sized,
    {
        let mut scratch = T::Buffer::default();
        self.retrieve(store, scratch.as_mut())
    }
}

impl<T> Field<T>
where
    T: DecodeValue,
{
    /// Loads and decodes this field, returning `None` when it has not been saved.
    pub fn retrieve<S>(
        &self,
        store: &mut S,
        scratch: &mut [u8],
    ) -> Result<Option<T>, RetrieveError<S::Error, T::Error>>
    where
        S: KeyValueStore + ?Sized,
    {
        let loaded = store
            .load(self.key, scratch)
            .map_err(RetrieveError::Backend)?;
        let len = match loaded {
            LoadOutcome::NotFound => return Ok(None),
            LoadOutcome::Loaded { len } => len,
            LoadOutcome::BufferTooSmall { required } => {
                return Err(RetrieveError::BufferTooSmall {
                    required,
                    available: scratch.len(),
                });
            }
        };
        if len > scratch.len() {
            return Err(RetrieveError::InvalidLoadedLength {
                reported: len,
                capacity: scratch.len(),
            });
        }
        T::decode_value(&scratch[..len])
            .map(Some)
            .map_err(RetrieveError::Decode)
    }
}
