use crate::Game;

use super::GameStatus;

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
