//! Versioned, checksummed envelopes for persisted byte records.
//!
//! The envelope protects format metadata and payload bytes. Domain components
//! remain responsible for encoding their payload and migrating schema versions.

mod error;

pub use error::{DecodeError, EncodeError};

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
///
/// # Errors
///
/// Returns [`EncodeError::PayloadTooLarge`] when the payload length cannot be
/// represented by the format, or [`EncodeError::OutputTooSmall`] when `output`
/// cannot hold the complete record.
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

    let header = Header::for_payload(schema_version, payload);
    output[..HEADER_LEN].copy_from_slice(&header.to_bytes());
    output[HEADER_LEN..required].copy_from_slice(payload);
    Ok(required)
}

/// Validates and decodes one complete record.
///
/// Trailing bytes are rejected because persistent records have an exact length;
/// callers must slice framing buffers before decoding.
///
/// # Errors
///
/// Returns a [`DecodeError`] when the input is shorter than the header, has an
/// invalid magic, an unsupported format version or flags or payload length,
/// its length does not match the declared payload, or the checksum differs.
pub fn decode(input: &[u8]) -> Result<Record<'_>, DecodeError> {
    let header = Header::parse(input)?;
    let payload = &input[HEADER_LEN..];
    let actual = checksum(&header.metadata(), payload);
    if actual != header.checksum {
        return Err(DecodeError::ChecksumMismatch {
            expected: header.checksum,
            actual,
        });
    }

    Ok(Record {
        schema_version: header.schema_version,
        payload,
    })
}

/// Computes CRC-32/ISO-HDLC for interoperability and diagnostics.
#[must_use]
pub fn crc32(bytes: &[u8]) -> u32 {
    !update_crc(!0, bytes)
}

/// The covered metadata: everything between the magic and the checksum.
const METADATA_LEN: usize = CHECKSUM_OFFSET - VERSION_OFFSET;

/// The fixed-width envelope header.
#[derive(Clone, Copy)]
struct Header {
    schema_version: u16,
    payload_len: u32,
    checksum: u32,
}

impl Header {
    /// Builds the header for `payload`, which must fit in `u32`.
    #[expect(
        clippy::cast_possible_truncation,
        reason = "`encode` rejects payloads over `u32::MAX` through `encoded_len` before building a header"
    )]
    fn for_payload(schema_version: u16, payload: &[u8]) -> Self {
        let mut header = Self {
            schema_version,
            payload_len: payload.len() as u32,
            checksum: 0,
        };
        header.checksum = checksum(&header.metadata(), payload);
        header
    }

    fn metadata(self) -> [u8; METADATA_LEN] {
        let mut bytes = [0; METADATA_LEN];
        bytes[0] = FORMAT_VERSION;
        bytes[FLAGS_OFFSET - VERSION_OFFSET] = SUPPORTED_FLAGS;
        bytes[SCHEMA_OFFSET - VERSION_OFFSET..LENGTH_OFFSET - VERSION_OFFSET]
            .copy_from_slice(&self.schema_version.to_le_bytes());
        bytes[LENGTH_OFFSET - VERSION_OFFSET..].copy_from_slice(&self.payload_len.to_le_bytes());
        bytes
    }

    fn to_bytes(self) -> [u8; HEADER_LEN] {
        let mut bytes = [0; HEADER_LEN];
        bytes[..MAGIC.len()].copy_from_slice(&MAGIC);
        bytes[VERSION_OFFSET..CHECKSUM_OFFSET].copy_from_slice(&self.metadata());
        bytes[CHECKSUM_OFFSET..].copy_from_slice(&self.checksum.to_le_bytes());
        bytes
    }

    /// Validates everything about `input` except the checksum.
    fn parse(input: &[u8]) -> Result<Self, DecodeError> {
        if input.len() < HEADER_LEN {
            return Err(DecodeError::TruncatedHeader {
                actual: input.len(),
            });
        }

        let mut found = [0; MAGIC.len()];
        found.copy_from_slice(&input[..MAGIC.len()]);
        if found != MAGIC {
            return Err(DecodeError::InvalidMagic { found });
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

        let declared_len = read_u32(input, LENGTH_OFFSET);
        let payload_len = usize::try_from(declared_len)
            .map_err(|_| DecodeError::PayloadLengthUnsupported { declared_len })?;
        let actual_len = input.len() - HEADER_LEN;
        if payload_len != actual_len {
            return Err(DecodeError::LengthMismatch {
                declared: declared_len,
                actual: actual_len,
            });
        }

        Ok(Self {
            schema_version: read_u16(input, SCHEMA_OFFSET),
            payload_len: declared_len,
            checksum: read_u32(input, CHECKSUM_OFFSET),
        })
    }
}

fn read_u16(input: &[u8], offset: usize) -> u16 {
    let mut bytes = [0; 2];
    bytes.copy_from_slice(&input[offset..offset + 2]);
    u16::from_le_bytes(bytes)
}

fn read_u32(input: &[u8], offset: usize) -> u32 {
    let mut bytes = [0; 4];
    bytes.copy_from_slice(&input[offset..offset + 4]);
    u32::from_le_bytes(bytes)
}

fn checksum(metadata: &[u8], payload: &[u8]) -> u32 {
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
