use core::fmt;

use super::HEADER_LEN;

/// A record-encoding failure.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EncodeError {
    /// The payload length cannot be represented by the format.
    PayloadTooLarge {
        /// The rejected payload length.
        len: usize,
    },

    /// The caller-provided output is too small.
    OutputTooSmall {
        /// The complete encoded length required.
        required: usize,
        /// The available output length.
        available: usize,
    },
}

impl fmt::Display for EncodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::PayloadTooLarge { len } => {
                write!(
                    formatter,
                    "payload length {len} exceeds the record format limit"
                )
            }
            Self::OutputTooSmall {
                required,
                available,
            } => write!(
                formatter,
                "record output requires {required} bytes but only {available} are available"
            ),
        }
    }
}

impl core::error::Error for EncodeError {}

/// A record-validation or decoding failure.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecodeError {
    /// Fewer than the record header's required bytes were provided.
    TruncatedHeader {
        /// The number of bytes provided.
        actual: usize,
    },

    /// The record does not begin with the expected magic bytes.
    InvalidMagic {
        /// The bytes found in the magic field.
        found: [u8; 4],
    },

    /// The envelope format version is not supported.
    UnsupportedFormatVersion {
        /// The version found in the record.
        found: u8,
    },

    /// Reserved format flags are set.
    UnsupportedFlags {
        /// The flags found in the record.
        found: u8,
    },

    /// The declared payload length cannot be represented by this target.
    PayloadLengthUnsupported {
        /// The length declared in the record.
        declared_len: u32,
    },

    /// The declared and actual payload lengths differ.
    LengthMismatch {
        /// The length declared in the record.
        declared: u32,
        /// The payload bytes actually provided.
        actual: usize,
    },

    /// The protected metadata or payload was corrupted.
    ChecksumMismatch {
        /// The checksum stored in the record.
        expected: u32,
        /// The checksum calculated from the record contents.
        actual: u32,
    },
}

impl fmt::Display for DecodeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TruncatedHeader { actual } => write!(
                formatter,
                "record header requires {HEADER_LEN} bytes but only {actual} were provided"
            ),
            Self::InvalidMagic { found } => write!(
                formatter,
                "invalid record magic {:02X}{:02X}{:02X}{:02X}",
                found[0], found[1], found[2], found[3]
            ),
            Self::UnsupportedFormatVersion { found } => {
                write!(formatter, "unsupported record format version {found}")
            }
            Self::UnsupportedFlags { found } => {
                write!(formatter, "unsupported record flags 0x{found:02X}")
            }
            Self::PayloadLengthUnsupported { declared_len } => write!(
                formatter,
                "declared payload length {declared_len} is unsupported on this target"
            ),
            Self::LengthMismatch { declared, actual } => write!(
                formatter,
                "record declares {declared} payload bytes but contains {actual}"
            ),
            Self::ChecksumMismatch { expected, actual } => write!(
                formatter,
                "record checksum mismatch: stored 0x{expected:08X}, calculated 0x{actual:08X}"
            ),
        }
    }
}

impl core::error::Error for DecodeError {}
