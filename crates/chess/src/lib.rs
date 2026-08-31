//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

#[macro_use]
mod macros;

mod game;
mod model;

pub use game::{
    DrawClaim, DrawClaims, DrawReason, FinalState, ForceMoveError, ForcedMove, Game, GameHistory,
    GameHistoryIter, GameStatus, GameSyncError, HistoryError, HistoryEvent, HistoryEventKind, HistoryHash, HistoryStep,
    InvalidPly, InvalidState, MoveCount, MoveError, MoveHash, MoveHistory, MoveHistoryIter, MoveStep,
    Ply,
};
pub use model::{
    AllSquares, Board, BoardDirection, BoardEdge, BoardPieces, CastlingRights, ChessMove, Color,
    File, FileOffset, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber, InvalidPromotion,
    InvalidSquare, ParseMoveError, ParseSquareError, Piece, PieceKind, Rank, RankOffset, Square,
    SquareCount, SquareIndex, SquareOffset, SquareRay, SquareSet, SquareSetSquares,
};
