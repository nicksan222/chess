//! Encoding contracts for values stored through typed fields.

mod error;
mod implementations;

pub use error::{ValueDecodeError, ValueEncodeError};

/// Encodes a typed value into caller-owned bytes.
///
/// Implementations must return the exact number of initialized bytes and must
/// not write outside that prefix. Stable persistence formats should use an
/// architecture-independent byte order.
pub trait EncodeValue {
    /// Encoding-specific failures.
    type Error;

    /// Encodes this value into `output` and returns the bytes written.
    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error>;
}

/// Reconstructs a typed value from its complete stored representation.
pub trait DecodeValue: Sized {
    /// Decoding-specific failures.
    type Error;

    /// Decodes one value from the complete `input` slice.
    fn decode_value(input: &[u8]) -> Result<Self, Self::Error>;
}

/// A value whose encoded form fits in a small, stack-owned buffer.
///
/// Implementing this trait enables the short forms of [`save!`](crate::save)
/// and [`retrieve!`](crate::retrieve), which create the scratch buffer
/// automatically. Variable-length values continue to use the explicit-buffer
/// macro forms.
pub trait InlineValue: EncodeValue + DecodeValue {
    /// Zero-initialized scratch storage large enough for every encoded value.
    type Buffer: AsRef<[u8]> + AsMut<[u8]> + Default;
}
