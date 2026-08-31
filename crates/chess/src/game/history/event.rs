use crate::{ChessMove, Color, DrawClaim, DrawReason, GameSyncError, MoveError};

/// A rejected operation retained in the authoritative game history.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum InvalidState {
    /// A move could not be applied.
    Move(MoveError),
    /// An incoming history step could not be synchronized.
    Synchronization(GameSyncError),
    /// A draw claim was not available.
    DrawClaim {
        /// The rejected claim.
        claim: DrawClaim,
    },
    /// A valid operation was attempted before newer invalid states were resolved.
    PendingInvalid,
}

/// A terminal result that permanently seals a game history.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FinalState {
    /// The side to move was checkmated.
    Checkmate {
        /// The player who delivered mate.
        winner: Color,
    },
    /// The side to move had no legal move and was not in check.
    Stalemate,
    /// The game ended under a draw rule.
    Draw {
        /// The rule that ended the game.
        reason: DrawReason,
    },
}

/// The category of an authoritative history event.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum HistoryEventKind {
    /// An accepted move.
    Move,
    /// An invalid state.
    Invalid,
    /// A terminal result.
    Final,
}

/// One authoritative fact in a game's chronological history.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HistoryEvent {
    /// A move accepted by the engine.
    Move(ChessMove),
    /// An invalid operation that must be resolved in reverse order.
    Invalid(InvalidState),
    /// The terminal result of the game.
    Final(FinalState),
}

impl HistoryEvent {
    /// Returns this event's category.
    #[must_use]
    pub const fn kind(self) -> HistoryEventKind {
        match self {
            Self::Move(_) => HistoryEventKind::Move,
            Self::Invalid(_) => HistoryEventKind::Invalid,
            Self::Final(_) => HistoryEventKind::Final,
        }
    }
}
