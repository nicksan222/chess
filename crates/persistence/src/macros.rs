/// Defines a consumer-owned inventory of typed persistent fields.
///
/// Each field binds one stable byte key to one Rust type. The generated struct
/// contains descriptors rather than values, making it cheap to construct and
/// impossible to retrieve a key as the wrong declared type.
///
/// ```
/// use chess_core::{Percentage, Toggle};
/// use persistence::persistence_schema;
///
/// persistence_schema! {
///     /// Every value persisted by this application.
///     pub struct Settings {
///         /// Whether board sounds are enabled.
///         pub sound: Toggle = b"settings/sound",
///         /// Display brightness.
///         pub brightness: Percentage = b"settings/brightness",
///     }
/// }
///
/// let settings = Settings::new();
/// assert_eq!(settings.sound.key(), b"settings/sound");
/// ```
///
/// Empty or duplicate keys are compile-time errors:
///
/// ```compile_fail
/// use persistence::persistence_schema;
///
/// persistence_schema! {
///     struct Invalid {
///         first: u8 = b"duplicate",
///         second: u16 = b"duplicate",
///     }
/// }
/// ```
#[macro_export]
macro_rules! persistence_schema {
    (
        $(#[$schema_meta:meta])*
        $visibility:vis struct $schema:ident {
            $(
                $(#[$field_meta:meta])*
                $field_visibility:vis $field:ident : $value:ty = $key:expr
            ),* $(,)?
        }
    ) => {
        const _: () = $crate::schema::validate_keys(&[$($key),*]);

        $(#[$schema_meta])*
        $visibility struct $schema {
            $(
                $(#[$field_meta])*
                $field_visibility $field: $crate::Field<$value>,
            )*
        }

        impl $schema {
            /// Creates the complete typed persistence schema.
            #[must_use]
            $visibility const fn new() -> Self {
                Self {
                    $($field: $crate::Field::new($key),)*
                }
            }
        }

        impl ::core::default::Default for $schema {
            fn default() -> Self {
                Self::new()
            }
        }
    };
}

/// Encodes and saves a value through a typed schema field.
///
/// Inline values such as integers, [`Toggle`](chess_core::Toggle), and
/// [`Percentage`](chess_core::Percentage) need no explicit scratch buffer:
///
/// ```no_run
/// # use chess_core::Toggle;
/// # use persistence::{KeyValueStore, persistence_schema, save};
/// # persistence_schema! { struct Settings { sound: Toggle = b"sound" } }
/// # fn example<S: KeyValueStore>(
/// #     store: &mut S,
/// # ) -> Result<(), persistence::SaveError<S::Error, persistence::ValueEncodeError>> {
/// let fields = Settings::new();
/// save!(store, fields.sound, Toggle::On)?;
/// # Ok(())
/// # }
/// ```
///
/// Variable-length values take a caller-owned buffer as the fourth argument.
/// The value expression is borrowed exactly once in both forms.
#[macro_export]
macro_rules! save {
    ($store:expr, $field:expr, $value:expr $(,)?) => {
        ($field).save_inline($store, &$value)
    };
    ($store:expr, $field:expr, $value:expr, $scratch:expr $(,)?) => {
        ($field).save($store, &$value, $scratch)
    };
}

/// Retrieves and decodes a value through a typed schema field.
///
/// Inline values need only the backend and field. Variable-length values take
/// a caller-owned scratch buffer as the third argument.
#[macro_export]
macro_rules! retrieve {
    ($store:expr, $field:expr $(,)?) => {
        ($field).retrieve_inline($store)
    };
    ($store:expr, $field:expr, $scratch:expr $(,)?) => {
        ($field).retrieve($store, $scratch)
    };
}
