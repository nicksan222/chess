//! Typed reasons a requested move cannot be played.

use core::fmt;

use crate::{Color, FinalState, Square};

/// A move that cannot be applied to the current board.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MoveError {
    /// The game has already ended.
    GameOver {
        /// The terminal result preventing further play.
        final_state: FinalState,
    },
    /// A newer invalid history event must be resolved first.
    PendingInvalid,
    /// The origin square is empty.
    NoPiece {
        /// The requested origin.
        square: Square,
    },
    /// The piece does not belong to the side to move.
    WrongSide {
        /// The expected color.
        expected: Color,
        /// The piece's color.
        actual: Color,
    },
    /// The destination is not legal for the piece.
    IllegalDestination {
        /// The move's origin.
        from: Square,
        /// The requested destination.
        to: Square,
    },
    /// A promotion was attached to a move that does not promote.
    UnexpectedPromotion,
    /// The requested promotion kind is not available.
    InvalidPromotion,
    /// A received promotion omitted the resulting piece kind.
    NonCanonicalPromotion,
    /// The piece object no longer matches the game board.
    StalePiece,
}

impl fmt::Display for MoveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::GameOver { final_state } => {
                write!(formatter, "the game has ended: {final_state:?}")
            }
            Self::PendingInvalid => {
                formatter.write_str("the latest invalid state must be resolved first")
            }
            Self::NoPiece { square } => write!(formatter, "there is no piece on {square}"),
            Self::WrongSide { expected, actual } => {
                write!(formatter, "it is {expected}'s turn, not {actual}'s")
            }
            Self::IllegalDestination { from, to } => {
                write!(formatter, "a move from {from} to {to} is not legal")
            }
            Self::UnexpectedPromotion => formatter.write_str("this move does not promote a pawn"),
            Self::InvalidPromotion => formatter.write_str("the promotion kind is invalid"),
            Self::NonCanonicalPromotion => {
                formatter.write_str("a synchronized promotion must include its piece kind")
            }
            Self::StalePiece => formatter.write_str("the piece no longer matches the board"),
        }
    }
}

impl_error!(MoveError);
