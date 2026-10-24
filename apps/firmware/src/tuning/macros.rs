//! Declares tuning groups once; see the `tuning!` invocation in `mod.rs`.

/// Generates one settings struct per group, the [`Tuning`](super::Tuning)
/// that holds them, and the [`Variable`](super::Variable) table behind
/// environment parsing and the env file. Each value is written as
///
/// ```text
/// /// What it controls.
/// field: <default> <unit> in <min>..=<max> from "FIRMWARE_NAME";
/// ```
///
/// with the default and range in the unit the variable is written in. The
/// unit also picks the field's type: `ms` is a [`Duration`](std::time::Duration),
/// `scans` a `u8` count. A default outside its range fails to compile.
macro_rules! tuning {
    ($(
        $(#[doc = $group_doc:literal])+
        $group:ident: $Group:ident {$(
            $(#[doc = $doc:literal])+
            $field:ident: $default:literal $unit:ident in $min:literal..=$max:literal from $name:literal;
        )+}
    )+) => {
        $(
            $(#[doc = $group_doc])+
            #[derive(Clone, Copy, Debug, Eq, PartialEq)]
            pub struct $Group {$(
                $(#[doc = $doc])+
                pub $field: tuning!(@type $unit),
            )+}

            impl $Group {
                /// The group's documentation, one line per doc line.
                pub const DOC: &str = concat!($($group_doc, "\n"),+);

                /// The values used when nothing is overridden.
                pub const DEFAULT: Self = Self {$(
                    $field: tuning!(@value $unit $default),
                )+};
            }

            impl Default for $Group {
                fn default() -> Self {
                    Self::DEFAULT
                }
            }

            $(const _: () = assert!($min <= $default && $default <= $max, concat!($name, " default is outside its range"));)+
        )+

        /// Every tuning group, as the firmware starts with it.
        #[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
        pub struct Tuning {$(
            $(#[doc = $group_doc])+
            pub $group: $Group,
        )+}

        impl Tuning {
            /// The values used when nothing is overridden.
            pub const DEFAULT: Self = Self {$(
                $group: $Group::DEFAULT,
            )+};

            /// Every variable, in declaration order.
            pub const VARIABLES: &[Variable] = &[$($(
                Variable {
                    name: $name,
                    group: $Group::DOC,
                    doc: concat!($($doc, "\n"),+),
                    default: $default,
                    min: $min,
                    max: $max,
                    unit: stringify!($unit),
                },
            )+)+];

            /// Sets the value `name` names, or returns `Ok(false)` for an
            /// unknown name.
            fn set(&mut self, name: &str, value: &str) -> Result<bool, TuningError> {
                match name {
                    $($($name => {
                        let number = parse($name, value, $min..=$max, stringify!($unit))?;
                        self.$group.$field = tuning!(@convert $unit number).ok_or_else(|| {
                            TuningError::OutOfRange {
                                name: $name,
                                value: value.to_owned(),
                                range: $min..=$max,
                                unit: stringify!($unit),
                            }
                        })?;
                        Ok(true)
                    })+)+
                    _ => Ok(false),
                }
            }
        }
    };

    (@type ms) => { ::std::time::Duration };
    (@type scans) => { u8 };
    (@value ms $value:literal) => { ::std::time::Duration::from_millis($value) };
    (@value scans $value:literal) => { $value };
    (@convert ms $number:ident) => { Some(::std::time::Duration::from_millis($number)) };
    (@convert scans $number:ident) => { u8::try_from($number).ok() };
}
