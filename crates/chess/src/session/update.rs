//! Observable session poll results.

use crate::{Color, GameStatus, HistoryStep};

/// The observable result of one session poll.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SessionUpdate {
    /// The current player has not supplied a move yet.
    Pending {
        /// The player whose turn remains pending.
        player: Color,
    },
    /// A player move was accepted and recorded.
    MovePlayed {
        /// The player that made the move.
        player: Color,
        /// The resulting authoritative history step.
        step: HistoryStep,
    },
    /// The game cannot accept player moves in its current state.
    Unavailable(GameStatus),
}
