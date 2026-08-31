//! Errors produced while accepting peer history steps.

use core::fmt;

use super::{HistoryError, MoveError};

/// An incoming move that failed synchronization or chess validation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GameSyncError {
    /// The move does not follow the local hash chain.
    History(HistoryError),
    /// The move is not legal in the local board.
    Move(MoveError),
}

impl fmt::Display for GameSyncError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::History(error) => error.fmt(formatter),
            Self::Move(error) => error.fmt(formatter),
        }
    }
}

impl core::error::Error for GameSyncError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::History(error) => Some(error),
            Self::Move(error) => Some(error),
        }
    }
}
