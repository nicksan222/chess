use chess_core::{Percentage, Toggle};
use persistence::{DecodeValue, EncodeValue, ValueDecodeError};

macro_rules! assert_integer_round_trip {
    ($type:ty, $value:expr) => {{
        let value: $type = $value;
        let mut output = [0xAA; 32];
        let written = value.encode_value(&mut output).expect("value encodes");

        assert_eq!(written, core::mem::size_of::<$type>());
        assert_eq!(&output[..written], &value.to_le_bytes());
        assert!(output[written..].iter().all(|byte| *byte == 0xAA));
        assert_eq!(
            <$type>::decode_value(&output[..written]).expect("value decodes"),
            value
        );
    }};
}

#[test]
fn integers_use_stable_little_endian_encodings() {
    assert_integer_round_trip!(u8, 0xA5);
    assert_integer_round_trip!(u16, 0xA1B2);
    assert_integer_round_trip!(u32, 0xA1B2_C3D4);
    assert_integer_round_trip!(u64, 0xA1B2_C3D4_E5F6_0718);
    assert_integer_round_trip!(u128, 0xA1B2_C3D4_E5F6_0718_192A_3B4C_5D6E_7F80);
    assert_integer_round_trip!(i8, -42);
    assert_integer_round_trip!(i16, -1234);
    assert_integer_round_trip!(i32, -123_456);
    assert_integer_round_trip!(i64, -1_234_567_890);
    assert_integer_round_trip!(i128, -12_345_678_901_234_567_890);
}

#[test]
fn byte_arrays_preserve_exact_length_and_contents() {
    let value = [0, 1, 127, 128, 255];
    let mut output = [0xAA; 8];

    assert_eq!(value.encode_value(&mut output), Ok(5));
    assert_eq!(&output[..5], &value);
    assert_eq!(<[u8; 5]>::decode_value(&output[..5]), Ok(value));
    assert_eq!(
        <[u8; 4]>::decode_value(&output[..5]),
        Err(ValueDecodeError::InvalidLength {
            expected: 4,
            actual: 5,
        })
    );
}

#[test]
fn too_small_encoding_buffers_are_unchanged() {
    let mut output = [0xAA; 3];
    let error = 42_u32
        .encode_value(&mut output)
        .expect_err("buffer is too small");

    assert_eq!(error.required(), 4);
    assert_eq!(error.available(), 3);
    assert_eq!(output, [0xAA; 3]);
}

#[test]
fn semantic_one_byte_values_validate_their_representations() {
    let mut output = [0; 1];

    assert_eq!(Toggle::On.encode_value(&mut output), Ok(1));
    assert_eq!(output, [1]);
    assert_eq!(Toggle::decode_value(&output), Ok(Toggle::On));
    assert_eq!(bool::decode_value(&[0]), Ok(false));
    assert_eq!(bool::decode_value(&[1]), Ok(true));
    assert_eq!(
        Toggle::decode_value(&[2]),
        Err(ValueDecodeError::InvalidDiscriminant { value: 2 })
    );
    assert_eq!(
        Percentage::decode_value(&[101]),
        Err(ValueDecodeError::OutOfRange {
            value: 101,
            maximum: 100,
        })
    );
    assert_eq!(
        Percentage::decode_value(&[]),
        Err(ValueDecodeError::InvalidLength {
            expected: 1,
            actual: 0,
        })
    );
}
