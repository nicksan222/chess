//! Errors produced while polling players or committing their moves.

use core::fmt;

use crate::{Color, MoveError, PlayerError};

/// A player or move failure produced by [`crate::GameSession::poll`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SessionError {
    /// A player failed while being polled.
    Player {
        /// The player whose move could not be obtained.
        player: Color,
        /// The underlying player failure.
        error: PlayerError,
    },
    /// A player submitted a move rejected by the authoritative game.
    MoveRejected {
        /// The player that submitted the move.
        player: Color,
        /// The rule failure returned by the game.
        error: MoveError,
    },
}

impl fmt::Display for SessionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Player { player, error } => {
                write!(formatter, "the {player} player failed: {error}")
            }
            Self::MoveRejected { player, error } => {
                write!(
                    formatter,
                    "the {player} player's move was rejected: {error}"
                )
            }
        }
    }
}

impl core::error::Error for SessionError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Player { error, .. } => Some(error),
            Self::MoveRejected { error, .. } => Some(error),
        }
    }
}
