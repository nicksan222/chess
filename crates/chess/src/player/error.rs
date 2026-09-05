//! Player polling failures.

use core::fmt;

use crate::ComputerError;

/// A failure produced while obtaining a player's move.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PlayerError {
    /// The local computer could not evaluate the position.
    Computer(ComputerError),
}

impl fmt::Display for PlayerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Computer(error) => write!(formatter, "the computer player failed: {error}"),
        }
    }
}

impl core::error::Error for PlayerError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Computer(error) => Some(error),
        }
    }
}
