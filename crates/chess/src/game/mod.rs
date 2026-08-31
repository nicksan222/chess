//! Playable game state, movement rules, and synchronized move history.

mod aggregate;
mod draw;
mod history;
mod movement;
mod position;
mod status;
mod sync_error;

pub use aggregate::Game;
pub use draw::DrawClaimError;
pub use history::{
    FinalState, GameHistory, GameHistoryIter, HistoryCount, HistoryError, HistoryEvent,
    HistoryEventKind, HistoryHash, HistoryStep, InvalidPly, InvalidState, Ply,
};
pub use movement::{ForceMoveError, ForcedMove, MoveError};
pub use status::{DrawClaim, DrawClaims, DrawReason, GameStatus};
pub use sync_error::GameSyncError;
