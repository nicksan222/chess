use core::fmt;

/// A typed field could not be encoded or stored.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SaveError<BackendError, ValueError> {
    /// Value encoding failed before the backend was called.
    Encode(ValueError),
    /// An encoder reported more bytes than its output buffer contains.
    InvalidEncodedLength {
        /// The length reported by the encoder.
        reported: usize,
        /// The scratch-buffer capacity.
        capacity: usize,
    },
    /// The persistence backend rejected the write.
    Backend(BackendError),
}

impl<S, V> fmt::Display for SaveError<S, V>
where
    S: fmt::Display,
    V: fmt::Display,
{
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Encode(error) => write!(formatter, "could not encode field: {error}"),
            Self::InvalidEncodedLength { reported, capacity } => write!(
                formatter,
                "field encoder reported {reported} bytes for a {capacity}-byte buffer"
            ),
            Self::Backend(error) => {
                write!(formatter, "persistence backend rejected field: {error}")
            }
        }
    }
}

impl<S, V> core::error::Error for SaveError<S, V>
where
    S: core::error::Error + 'static,
    V: core::error::Error + 'static,
{
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Encode(error) => Some(error),
            Self::Backend(error) => Some(error),
            Self::InvalidEncodedLength { .. } => None,
        }
    }
}

/// A typed field could not be loaded or decoded.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RetrieveError<BackendError, ValueError> {
    /// The persistence backend failed.
    Backend(BackendError),
    /// The caller's scratch buffer cannot hold the complete stored value.
    BufferTooSmall {
        /// The complete stored length required.
        required: usize,
        /// The provided scratch-buffer length.
        available: usize,
    },
    /// A backend reported more loaded bytes than the output buffer contains.
    InvalidLoadedLength {
        /// The length reported by the backend.
        reported: usize,
        /// The scratch-buffer capacity.
        capacity: usize,
    },
    /// The stored bytes are not a valid representation of the field's type.
    Decode(ValueError),
}

impl<S, V> fmt::Display for RetrieveError<S, V>
where
    S: fmt::Display,
    V: fmt::Display,
{
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Backend(error) => {
                write!(
                    formatter,
                    "persistence backend could not load field: {error}"
                )
            }
            Self::BufferTooSmall {
                required,
                available,
            } => write!(
                formatter,
                "stored field requires {required} bytes but only {available} are available"
            ),
            Self::InvalidLoadedLength { reported, capacity } => write!(
                formatter,
                "persistence backend reported {reported} bytes for a {capacity}-byte buffer"
            ),
            Self::Decode(error) => write!(formatter, "could not decode field: {error}"),
        }
    }
}

impl<S, V> core::error::Error for RetrieveError<S, V>
where
    S: core::error::Error + 'static,
    V: core::error::Error + 'static,
{
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Backend(error) => Some(error),
            Self::Decode(error) => Some(error),
            Self::BufferTooSmall { .. } | Self::InvalidLoadedLength { .. } => None,
        }
    }
}
