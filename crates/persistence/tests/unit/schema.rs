use core::convert::Infallible;

use chess_core::{Percentage, Toggle};
use persistence::{
    DecodeValue, EncodeValue, InlineValue, KeyValueStore, LoadOutcome, RetrieveError, SaveError,
    ValueDecodeError, ValueEncodeError, persistence_schema, retrieve, save,
};

use crate::common::MemoryStore;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Theme {
    Light,
    Dark,
}

impl EncodeValue for Theme {
    type Error = ValueEncodeError;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        match self {
            Self::Light => 0_u8,
            Self::Dark => 1_u8,
        }
        .encode_value(output)
    }
}

impl DecodeValue for Theme {
    type Error = ValueDecodeError;

    fn decode_value(input: &[u8]) -> Result<Self, Self::Error> {
        match u8::decode_value(input)? {
            0 => Ok(Self::Light),
            1 => Ok(Self::Dark),
            value => Err(ValueDecodeError::InvalidDiscriminant { value }),
        }
    }
}

impl InlineValue for Theme {
    type Buffer = [u8; 1];
}

persistence_schema! {
    struct Settings {
        sound: Toggle = b"settings/sound",
        brightness: Percentage = b"settings/brightness",
        launches: u32 = b"statistics/launches",
        theme: Theme = b"settings/theme",
    }
}

#[test]
fn schema_fields_save_and_retrieve_their_declared_types() {
    let fields = Settings::new();
    let mut store = MemoryStore::new();
    let mut scratch = [0; 8];

    save!(&mut store, fields.sound, Toggle::On).expect("sound saves");
    save!(
        &mut store,
        fields.brightness,
        Percentage::new(73).expect("valid percentage"),
        &mut scratch,
    )
    .expect("brightness saves");
    fields
        .launches
        .save(&mut store, &42, &mut scratch)
        .expect("counter saves");
    save!(&mut store, fields.theme, Theme::Dark).expect("theme saves");

    assert_eq!(
        retrieve!(&mut store, fields.sound).expect("sound loads"),
        Some(Toggle::On)
    );
    assert_eq!(
        fields
            .brightness
            .retrieve(&mut store, &mut scratch)
            .expect("brightness loads"),
        Percentage::new(73).ok()
    );
    assert_eq!(
        retrieve!(&mut store, fields.launches, &mut scratch).expect("counter loads"),
        Some(42)
    );
    assert_eq!(
        retrieve!(&mut store, fields.theme).expect("theme loads"),
        Some(Theme::Dark)
    );
}

#[test]
fn missing_typed_field_is_none() {
    let mut store = MemoryStore::new();
    let mut scratch = [0; 1];

    assert_eq!(
        Settings::new().sound.retrieve(&mut store, &mut scratch),
        Ok(None)
    );
}

#[test]
fn malformed_values_are_rejected_by_the_declared_type() {
    let fields = Settings::new();
    let mut store = MemoryStore::new();
    let mut scratch = [0; 1];
    store
        .store(fields.sound.key(), &[2])
        .expect("raw fixture stores");

    assert_eq!(
        fields.sound.retrieve(&mut store, &mut scratch),
        Err(RetrieveError::Decode(
            ValueDecodeError::InvalidDiscriminant { value: 2 }
        ))
    );

    store
        .store(fields.brightness.key(), &[101])
        .expect("raw fixture stores");
    assert_eq!(
        fields.brightness.retrieve(&mut store, &mut scratch),
        Err(RetrieveError::Decode(ValueDecodeError::OutOfRange {
            value: 101,
            maximum: 100,
        }))
    );
}

#[test]
fn scratch_capacity_errors_are_precise_and_do_not_write() {
    let fields = Settings::new();
    let mut store = MemoryStore::new();
    let mut short = [0xAA; 3];

    let error = fields
        .launches
        .save(&mut store, &42, &mut short)
        .expect_err("scratch is too small");
    let SaveError::Encode(error) = error else {
        panic!("expected an encoding error");
    };
    assert_eq!(error.required(), 4);
    assert_eq!(error.available(), 3);
    assert!(
        !store
            .contains(fields.launches.key())
            .expect("contains succeeds")
    );
    assert_eq!(short, [0xAA; 3]);

    store
        .store(fields.launches.key(), &42_u32.to_le_bytes())
        .expect("raw fixture stores");
    assert_eq!(
        fields.launches.retrieve(&mut store, &mut short),
        Err(RetrieveError::BufferTooSmall {
            required: 4,
            available: 3,
        })
    );
}

struct InvalidEncoder;

impl EncodeValue for InvalidEncoder {
    type Error = Infallible;

    fn encode_value(&self, output: &mut [u8]) -> Result<usize, Self::Error> {
        Ok(output.len() + 1)
    }
}

struct InvalidBackend;

impl KeyValueStore for InvalidBackend {
    type Error = Infallible;

    fn value_len(&mut self, _key: &[u8]) -> Result<Option<usize>, Self::Error> {
        Ok(Some(2))
    }

    fn load(&mut self, _key: &[u8], output: &mut [u8]) -> Result<LoadOutcome, Self::Error> {
        Ok(LoadOutcome::Loaded {
            len: output.len() + 1,
        })
    }

    fn store(&mut self, _key: &[u8], _value: &[u8]) -> Result<(), Self::Error> {
        Ok(())
    }

    fn remove(&mut self, _key: &[u8]) -> Result<bool, Self::Error> {
        Ok(false)
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        Ok(())
    }
}

impl DecodeValue for InvalidEncoder {
    type Error = Infallible;

    fn decode_value(_input: &[u8]) -> Result<Self, Self::Error> {
        Ok(Self)
    }
}

#[test]
fn invalid_extension_contracts_return_errors_instead_of_panicking() {
    let field = persistence::Field::<InvalidEncoder>::new(b"invalid");
    let mut store = MemoryStore::new();
    let mut scratch = [0; 2];

    assert!(matches!(
        field.save(&mut store, &InvalidEncoder, &mut scratch),
        Err(SaveError::InvalidEncodedLength {
            reported: 3,
            capacity: 2,
        })
    ));
    assert!(matches!(
        field.retrieve(&mut InvalidBackend, &mut scratch),
        Err(RetrieveError::InvalidLoadedLength {
            reported: 3,
            capacity: 2,
        })
    ));
}
