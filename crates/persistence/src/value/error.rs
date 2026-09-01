use core::fmt;

/// A built-in value could not be encoded into the provided buffer.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ValueEncodeError {
    required: usize,
    available: usize,
}

impl ValueEncodeError {
    pub(super) const fn new(required: usize, available: usize) -> Self {
        Self {
            required,
            available,
        }
    }

    /// Returns the number of bytes required by the value.
    #[must_use]
    pub const fn required(self) -> usize {
        self.required
    }

    /// Returns the available output length.
    #[must_use]
    pub const fn available(self) -> usize {
        self.available
    }
}

impl fmt::Display for ValueEncodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "value encoding requires {} bytes but only {} are available",
            self.required, self.available
        )
    }
}

impl core::error::Error for ValueEncodeError {}

/// A built-in value's stored representation is invalid.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ValueDecodeError {
    /// The representation has a different length than the type requires.
    InvalidLength {
        /// The exact expected length.
        expected: usize,
        /// The stored length.
        actual: usize,
    },
    /// A one-byte representation contains an unsupported discriminant.
    InvalidDiscriminant {
        /// The rejected byte.
        value: u8,
    },
    /// A numeric representation violates the value type's range.
    OutOfRange {
        /// The rejected value.
        value: u8,
        /// The greatest accepted value.
        maximum: u8,
    },
}

impl fmt::Display for ValueDecodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidLength { expected, actual } => write!(
                formatter,
                "value representation requires exactly {expected} bytes but contains {actual}"
            ),
            Self::InvalidDiscriminant { value } => {
                write!(formatter, "invalid value discriminant 0x{value:02X}")
            }
            Self::OutOfRange { value, maximum } => {
                write!(formatter, "value {value} exceeds maximum {maximum}")
            }
        }
    }
}

impl core::error::Error for ValueDecodeError {}
