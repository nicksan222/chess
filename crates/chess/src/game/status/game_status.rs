use crate::Color;

use super::{DrawClaims, DrawReason};

/// Whether the side to move can still play, may claim a draw, or the game ended.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GameStatus {
    /// At least one legal move remains and no draw is currently claimable.
    InProgress,
    /// Play may continue, but the side to move may claim one or more draws.
    DrawClaimAvailable(DrawClaims),
    /// The side to move is in check and has no legal move.
    Checkmate {
        /// The player who delivered mate.
        winner: Color,
    },
    /// The side to move is not in check and has no legal move.
    Stalemate,
    /// The game ended in a draw.
    Draw {
        /// The rule that ended the game.
        reason: DrawReason,
    },
}

impl GameStatus {
    /// Returns whether this status ends the game.
    #[must_use]
    pub const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Checkmate { .. } | Self::Stalemate | Self::Draw { .. }
        )
    }
}
