use crate::{Color, Game};

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

impl Game {
    /// Returns whether the current position is checkmate, stalemate, or still playable.
    #[must_use]
    pub fn status(&self) -> GameStatus {
        match (self.is_in_check(), self.legal_moves().next().is_some()) {
            (_, true) => GameStatus::InProgress,
            (true, false) => GameStatus::Checkmate {
                winner: self.side_to_move().opposite(),
            },
            (false, false) => GameStatus::Stalemate,
        }
    }

    /// Returns whether the side to move is checkmated.
    #[must_use]
    pub fn is_checkmate(&self) -> bool {
        matches!(self.status(), GameStatus::Checkmate { .. })
    }

    /// Returns whether the position is stalemate.
    #[must_use]
    pub fn is_stalemate(&self) -> bool {
        matches!(self.status(), GameStatus::Stalemate)
    }
}
