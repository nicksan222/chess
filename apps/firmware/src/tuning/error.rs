//! Why a tuning variable was rejected.

use std::{error::Error, fmt, ops::RangeInclusive};

/// A tuning variable whose value cannot be used. The firmware refuses to
/// start with it rather than guess.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TuningError {
    /// The value is not a whole, non-negative number.
    NotANumber {
        name: &'static str,
        value: String,
        range: RangeInclusive<u64>,
        unit: &'static str,
    },
    /// The value is a number outside the variable's range.
    OutOfRange {
        name: &'static str,
        value: String,
        range: RangeInclusive<u64>,
        unit: &'static str,
    },
}

impl fmt::Display for TuningError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let (problem, name, value, range, unit) = match self {
            Self::NotANumber {
                name,
                value,
                range,
                unit,
            } => ("is not a whole number", name, value, range, unit),
            Self::OutOfRange {
                name,
                value,
                range,
                unit,
            } => ("is out of range", name, value, range, unit),
        };
        write!(
            formatter,
            "{name}={value:?} {problem}; expected {} to {} {unit}",
            range.start(),
            range.end()
        )
    }
}

impl Error for TuningError {}

/// Parses `value` as a number of `unit` within `range`.
pub(super) fn parse(
    name: &'static str,
    value: &str,
    range: RangeInclusive<u64>,
    unit: &'static str,
) -> Result<u64, TuningError> {
    let Ok(number) = value.trim().parse::<u64>() else {
        return Err(TuningError::NotANumber {
            name,
            value: value.to_owned(),
            range,
            unit,
        });
    };
    if !range.contains(&number) {
        return Err(TuningError::OutOfRange {
            name,
            value: value.to_owned(),
            range,
            unit,
        });
    }
    Ok(number)
}
