//! Versioned, checksummed envelopes for persisted byte records.
//!
//! The envelope protects format metadata and payload bytes. Domain components
//! remain responsible for encoding their payload and migrating schema versions.

use core::fmt;

/// The encoded record magic bytes.
pub const MAGIC: [u8; 4] = *b"CHDB";

/// The envelope format version emitted and accepted by this implementation.
pub const FORMAT_VERSION: u8 = 1;

/// The encoded header length in bytes.
pub const HEADER_LEN: usize = 16;

const SUPPORTED_FLAGS: u8 = 0;
const VERSION_OFFSET: usize = 4;
const FLAGS_OFFSET: usize = 5;
const SCHEMA_OFFSET: usize = 6;
const LENGTH_OFFSET: usize = 8;
const CHECKSUM_OFFSET: usize = 12;

/// A decoded record borrowing its payload from the encoded input.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Record<'a> {
    schema_version: u16,
    payload: &'a [u8],
}

impl<'a> Record<'a> {
    /// Returns the domain-owned schema version.
    #[must_use]
    pub const fn schema_version(self) -> u16 {
        self.schema_version
    }

    /// Returns the validated payload bytes.
    #[must_use]
    pub const fn payload(self) -> &'a [u8] {
        self.payload
    }
}

/// Returns the encoded size for `payload_len`, or `None` when it cannot be
/// represented by the format or the target's `usize`.
#[must_use]
pub const fn encoded_len(payload_len: usize) -> Option<usize> {
    if payload_len > u32::MAX as usize {
        return None;
    }
    payload_len.checked_add(HEADER_LEN)
}

/// Encodes one schema-versioned payload into caller-provided storage.
///
/// The output is left unchanged on error. Bytes after the returned encoded
/// length are not modified.
pub fn encode(
    schema_version: u16,
    payload: &[u8],
    output: &mut [u8],
) -> Result<usize, EncodeError> {
    let required =
        encoded_len(payload.len()).ok_or(EncodeError::PayloadTooLarge { len: payload.len() })?;
    if output.len() < required {
        return Err(EncodeError::OutputTooSmall {
            required,
            available: output.len(),
        });
    }

    let payload_len = payload.len() as u32;
    let metadata = metadata(schema_version, payload_len);
    let checksum = checksum(&metadata, payload);

    output[..4].copy_from_slice(&MAGIC);
    output[VERSION_OFFSET..CHECKSUM_OFFSET].copy_from_slice(&metadata);
    output[CHECKSUM_OFFSET..HEADER_LEN].copy_from_slice(&checksum.to_le_bytes());
    output[HEADER_LEN..required].copy_from_slice(payload);
    Ok(required)
}

/// Validates and decodes one complete record.
///
/// Trailing bytes are rejected because persistent records have an exact length;
/// callers must slice framing buffers before decoding.
pub fn decode(input: &[u8]) -> Result<Record<'_>, DecodeError> {
    if input.len() < HEADER_LEN {
        return Err(DecodeError::TruncatedHeader {
            actual: input.len(),
        });
    }

    let found_magic: [u8; 4] = input[..4]
        .try_into()
        .expect("the header length was validated above");
    if found_magic != MAGIC {
        return Err(DecodeError::InvalidMagic { found: found_magic });
    }

    let format_version = input[VERSION_OFFSET];
    if format_version != FORMAT_VERSION {
        return Err(DecodeError::UnsupportedFormatVersion {
            found: format_version,
        });
    }

    let flags = input[FLAGS_OFFSET];
    if flags != SUPPORTED_FLAGS {
        return Err(DecodeError::UnsupportedFlags { found: flags });
    }

    let schema_version = u16::from_le_bytes(
        input[SCHEMA_OFFSET..LENGTH_OFFSET]
            .try_into()
            .expect("schema field has a fixed width"),
    );
    let declared_len = u32::from_le_bytes(
        input[LENGTH_OFFSET..CHECKSUM_OFFSET]
            .try_into()
            .expect("length field has a fixed width"),
    );
    let payload_len = usize::try_from(declared_len)
        .map_err(|_| DecodeError::PayloadLengthUnsupported { declared_len })?;
    let actual_len = input.len() - HEADER_LEN;
    if payload_len != actual_len {
        return Err(DecodeError::LengthMismatch {
            declared: declared_len,
            actual: actual_len,
        });
    }

    let expected = u32::from_le_bytes(
        input[CHECKSUM_OFFSET..HEADER_LEN]
            .try_into()
            .expect("checksum field has a fixed width"),
    );
    let metadata: [u8; 8] = input[VERSION_OFFSET..CHECKSUM_OFFSET]
        .try_into()
        .expect("metadata has a fixed width");
    let payload = &input[HEADER_LEN..];
    let actual = checksum(&metadata, payload);
    if actual != expected {
        return Err(DecodeError::ChecksumMismatch { expected, actual });
    }

    Ok(Record {
        schema_version,
        payload,
    })
}

/// Computes CRC-32/ISO-HDLC for interoperability and diagnostics.
#[must_use]
pub fn crc32(bytes: &[u8]) -> u32 {
    !update_crc(!0, bytes)
}

fn metadata(schema_version: u16, payload_len: u32) -> [u8; 8] {
    let mut metadata = [0; 8];
    metadata[0] = FORMAT_VERSION;
    metadata[1] = SUPPORTED_FLAGS;
    metadata[2..4].copy_from_slice(&schema_version.to_le_bytes());
    metadata[4..8].copy_from_slice(&payload_len.to_le_bytes());
    metadata
}

fn checksum(metadata: &[u8; 8], payload: &[u8]) -> u32 {
    !update_crc(update_crc(!0, metadata), payload)
}

fn update_crc(mut crc: u32, bytes: &[u8]) -> u32 {
    for &byte in bytes {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            let mask = 0_u32.wrapping_sub(crc & 1);
            crc = (crc >> 1) ^ (0xEDB8_8320 & mask);
        }
    }
    crc
}

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
    /// Fewer than [`HEADER_LEN`] bytes were provided.
    TruncatedHeader {
        /// The number of bytes provided.
        actual: usize,
    },

    /// The record does not begin with [`MAGIC`].
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
