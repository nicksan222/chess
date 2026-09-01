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
