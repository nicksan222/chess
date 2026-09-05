//! Computer player failures.

use core::fmt;

use crate::ChessMove;

/// A failure while translating or searching a computer position.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ComputerError {
    /// An en-passant marker did not identify a valid double pawn push.
    InconsistentEnPassant,
    /// The underlying engine returned an invalid square.
    InvalidSquare,
    /// The engine suggested a move that is not legal in the domain position.
    ///
    /// The offending move is returned so callers can log or diagnose the
    /// engine/domain divergence. It is never played.
    IllegalMove(ChessMove),
    /// The engine resigned while the domain position still has legal moves.
    ///
    /// The domain has no resignation result, so a resignation with moves
    /// available is reported rather than silently replaced.
    Resigned,
}

impl fmt::Display for ComputerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InconsistentEnPassant => formatter
                .write_str("the en-passant target does not describe a valid double pawn push"),
            Self::InvalidSquare => formatter.write_str("the computer returned an invalid square"),
            Self::IllegalMove(chess_move) => {
                write!(
                    formatter,
                    "the computer suggested illegal move {chess_move}"
                )
            }
            Self::Resigned => formatter.write_str("the computer resigned while legal moves remain"),
        }
    }
}

impl core::error::Error for ComputerError {}
