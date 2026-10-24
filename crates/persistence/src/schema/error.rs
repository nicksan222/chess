use core::fmt;

/// A reported byte count that exceeds the buffer it claims to fill.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct LengthViolation {
    reported: usize,
    capacity: usize,
}

/// Returns `reported` when it fits within `capacity` bytes.
pub(super) const fn checked_prefix(
    reported: usize,
    capacity: usize,
) -> Result<usize, LengthViolation> {
    if reported > capacity {
        Err(LengthViolation { reported, capacity })
    } else {
        Ok(reported)
    }
}

/// Implements `Error` for a backend/value error pair, exposing the listed
/// single-field variants as the source.
macro_rules! impl_error_source {
    ($name:ident: $($variant:ident),+ $(,)?) => {
        impl<S, V> core::error::Error for $name<S, V>
        where
            S: core::error::Error + 'static,
            V: core::error::Error + 'static,
        {
            fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
                match self {
                    $(Self::$variant(error) => Some(error),)+
                    _ => None,
                }
            }
        }
    };
}

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

impl_error_source!(SaveError: Encode, Backend);

impl<S, V> From<LengthViolation> for SaveError<S, V> {
    fn from(LengthViolation { reported, capacity }: LengthViolation) -> Self {
        Self::InvalidEncodedLength { reported, capacity }
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

impl_error_source!(RetrieveError: Backend, Decode);

impl<S, V> From<LengthViolation> for RetrieveError<S, V> {
    fn from(LengthViolation { reported, capacity }: LengthViolation) -> Self {
        Self::InvalidLoadedLength { reported, capacity }
    }
}
