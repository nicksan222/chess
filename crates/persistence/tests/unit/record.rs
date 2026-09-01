use persistence::{
    KeyValueStore, LoadOutcome,
    record::{
        DecodeError, EncodeError, FORMAT_VERSION, HEADER_LEN, MAGIC, crc32, decode, encode,
        encoded_len,
    },
};

use crate::common::MemoryStore;

fn encoded(schema_version: u16, payload: &[u8]) -> Vec<u8> {
    let mut output = vec![0; encoded_len(payload.len()).expect("representable length")];
    let written = encode(schema_version, payload, &mut output).expect("encoding succeeds");
    assert_eq!(written, output.len());
    output
}

#[test]
fn crc32_matches_standard_check_value() {
    assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
    assert_eq!(crc32(b""), 0);
}

#[test]
fn encoding_layout_and_decoding_round_trip() {
    let payload = b"calibration-v1";
    let bytes = encoded(0x1234, payload);

    assert_eq!(&bytes[..4], &MAGIC);
    assert_eq!(bytes[4], FORMAT_VERSION);
    assert_eq!(bytes[5], 0);
    assert_eq!(&bytes[6..8], &0x1234_u16.to_le_bytes());
    assert_eq!(&bytes[8..12], &(payload.len() as u32).to_le_bytes());
    assert_eq!(bytes.len(), HEADER_LEN + payload.len());

    let record = decode(&bytes).expect("record is valid");
    assert_eq!(record.schema_version(), 0x1234);
    assert_eq!(record.payload(), payload);
}

#[test]
fn empty_payload_is_distinct_and_valid() {
    let bytes = encoded(0, b"");
    let record = decode(&bytes).expect("record is valid");

    assert_eq!(bytes.len(), HEADER_LEN);
    assert_eq!(record.schema_version(), 0);
    assert!(record.payload().is_empty());
}

#[test]
fn output_errors_never_modify_the_buffer() {
    let mut output = [0xAA; HEADER_LEN + 2];
    let original = output;

    let error = encode(1, b"abc", &mut output).expect_err("output is too small");

    assert_eq!(
        error,
        EncodeError::OutputTooSmall {
            required: HEADER_LEN + 3,
            available: HEADER_LEN + 2,
        }
    );
    assert_eq!(output, original);
}

#[test]
fn successful_encoding_does_not_touch_trailing_capacity() {
    let mut output = [0xCC; 64];
    let written = encode(7, b"game", &mut output).expect("encoding succeeds");

    assert_eq!(written, HEADER_LEN + 4);
    assert!(output[written..].iter().all(|byte| *byte == 0xCC));
    assert_eq!(
        decode(&output[..written])
            .expect("record is valid")
            .payload(),
        b"game"
    );
}

#[test]
fn truncated_headers_are_rejected_at_every_length() {
    for len in 0..HEADER_LEN {
        assert_eq!(
            decode(&[0; HEADER_LEN][..len]),
            Err(DecodeError::TruncatedHeader { actual: len })
        );
    }
}

#[test]
fn format_identity_and_reserved_flags_are_validated() {
    let valid = encoded(1, b"payload");

    let mut bad_magic = valid.clone();
    bad_magic[..4].copy_from_slice(b"NOPE");
    assert_eq!(
        decode(&bad_magic),
        Err(DecodeError::InvalidMagic { found: *b"NOPE" })
    );

    let mut bad_version = valid.clone();
    bad_version[4] = FORMAT_VERSION + 1;
    assert_eq!(
        decode(&bad_version),
        Err(DecodeError::UnsupportedFormatVersion {
            found: FORMAT_VERSION + 1,
        })
    );

    let mut bad_flags = valid;
    bad_flags[5] = 0x80;
    assert_eq!(
        decode(&bad_flags),
        Err(DecodeError::UnsupportedFlags { found: 0x80 })
    );
}

#[test]
fn declared_length_must_match_exact_input_length() {
    let valid = encoded(1, b"abc");

    let mut too_large = valid.clone();
    too_large[8..12].copy_from_slice(&4_u32.to_le_bytes());
    assert_eq!(
        decode(&too_large),
        Err(DecodeError::LengthMismatch {
            declared: 4,
            actual: 3,
        })
    );

    let mut with_trailing_byte = valid;
    with_trailing_byte.push(0);
    assert_eq!(
        decode(&with_trailing_byte),
        Err(DecodeError::LengthMismatch {
            declared: 3,
            actual: 4,
        })
    );
}

#[test]
fn checksum_protects_schema_metadata_payload_and_checksum_field() {
    for index in [6, 7, 16, 17, 12, 13, 14, 15] {
        let mut bytes = encoded(0x1234, b"payload");
        bytes[index] ^= 0x01;

        assert!(matches!(
            decode(&bytes),
            Err(DecodeError::ChecksumMismatch { .. })
        ));
    }
}

#[test]
fn deterministic_payload_sample_round_trips() {
    let mut state = 0xDEAD_BEEF_u32;

    for len in 0..512 {
        let mut payload = Vec::with_capacity(len);
        for _ in 0..len {
            state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
            payload.push(state as u8);
        }

        let bytes = encoded(len as u16, &payload);
        let record = decode(&bytes).expect("record is valid");
        assert_eq!(record.schema_version(), len as u16);
        assert_eq!(record.payload(), payload);
    }
}

#[test]
fn record_envelopes_round_trip_through_key_value_storage() {
    let bytes = encoded(3, b"saved-game");
    let mut store = MemoryStore::new();
    store
        .store(b"games/latest", &bytes)
        .expect("store succeeds");

    let required = store
        .value_len(b"games/latest")
        .expect("length succeeds")
        .expect("value exists");
    let mut loaded = vec![0; required];
    assert_eq!(
        store
            .load(b"games/latest", &mut loaded)
            .expect("load succeeds"),
        LoadOutcome::Loaded { len: required }
    );

    let record = decode(&loaded).expect("stored record remains valid");
    assert_eq!(record.schema_version(), 3);
    assert_eq!(record.payload(), b"saved-game");
}

#[test]
fn encoded_length_rejects_unrepresentable_payloads() {
    assert_eq!(encoded_len(0), Some(HEADER_LEN));

    #[cfg(target_pointer_width = "64")]
    assert_eq!(encoded_len(u32::MAX as usize + 1), None);
}
