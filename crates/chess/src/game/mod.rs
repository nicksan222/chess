//! Playable game state, movement rules, and synchronized move history.

mod aggregate;
mod history;
mod movement;
mod position;
mod status;
mod sync_error;

pub use aggregate::Game;
pub use history::{
    FinalState, GameHistory, GameHistoryIter, HistoryError, HistoryEvent, HistoryHash, HistoryStep,
    InvalidPly, InvalidState, MoveCount, MoveHash, MoveHistory, MoveHistoryIter, MoveStep, Ply,
};
pub use movement::{ForceMoveError, ForcedMove, MoveError};
pub use status::{DrawClaim, DrawClaims, DrawReason, GameStatus};
pub use sync_error::GameSyncError;
