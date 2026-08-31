mod evaluation;

use crate::Color;

/// Whether the side to move can still play, or the game has ended.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GameStatus {
    /// At least one legal move remains.
    InProgress,
    /// The side to move is in check and has no legal move.
    Checkmate {
        /// The player who delivered mate.
        winner: Color,
    },
    /// The side to move is not in check and has no legal move.
    Stalemate,
}
