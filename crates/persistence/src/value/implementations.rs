use chess_core::{Percentage, Toggle};

use super::{DecodeValue, EncodeValue, InlineValue, ValueDecodeError, ValueEncodeError};

fn encode_bytes(bytes: &[u8], output: &mut [u8]) -> Result<usize, ValueEncodeError> {
    if output.len() < bytes.len() {
        return Err(ValueEncodeError::new(bytes.len(), output.len()));
    }
    output[..bytes.len()].copy_from_slice(bytes);
    Ok(bytes.len())
}

fn exact<const N: usize>(input: &[u8]) -> Result<[u8; N], ValueDecodeError> {
    input
        .try_into()
        .map_err(|_| ValueDecodeError::InvalidLength {
            expected: N,
            actual: input.len(),
        })
}

macro_rules! integer_codec {
    ($($type:ty),+ $(,)?) => {
        $(
            impl EncodeValue for $type {
                type Error = ValueEncodeError;

                fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
                    encode_bytes(&self.to_le_bytes(), output)
                }
            }

            impl DecodeValue for $type {
                type Error = ValueDecodeError;

                fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
                    Ok(Self::from_le_bytes(exact(input)?))
                }
            }

            impl InlineValue for $type {
                type Buffer = [u8; core::mem::size_of::<$type>()];
            }
        )+
    };
}

integer_codec!(u8, u16, u32, u64, u128, i8, i16, i32, i64, i128);

impl<const N: usize> EncodeValue for [u8; N] {
    type Error = ValueEncodeError;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        encode_bytes(self, output)
    }
}

impl<const N: usize> DecodeValue for [u8; N] {
    type Error = ValueDecodeError;

    fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
        exact(input)
    }
}

impl<const N: usize> InlineValue for [u8; N]
where
    [u8; N]: Default,
{
    type Buffer = [u8; N];
}

impl EncodeValue for bool {
    type Error = ValueEncodeError;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        u8::from(*self).encode_value(output)
    }
}

impl DecodeValue for bool {
    type Error = ValueDecodeError;

    fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
        match u8::decode_value(input)? {
            0 => Ok(false),
            1 => Ok(true),
            value => Err(ValueDecodeError::InvalidDiscriminant { value }),
        }
    }
}

impl InlineValue for bool {
    type Buffer = [u8; 1];
}

impl EncodeValue for Toggle {
    type Error = ValueEncodeError;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        bool::from(*self).encode_value(output)
    }
}

impl DecodeValue for Toggle {
    type Error = ValueDecodeError;

    fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
        bool::decode_value(input).map(Self::from)
    }
}

impl InlineValue for Toggle {
    type Buffer = [u8; 1];
}

impl EncodeValue for Percentage {
    type Error = ValueEncodeError;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        self.get().encode_value(output)
    }
}

impl DecodeValue for Percentage {
    type Error = ValueDecodeError;

    fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
        let value = u8::decode_value(input)?;
        Self::new(value).map_err(|_| ValueDecodeError::OutOfRange {
            value,
            maximum: 100,
        })
    }
}

impl InlineValue for Percentage {
    type Buffer = [u8; 1];
}
