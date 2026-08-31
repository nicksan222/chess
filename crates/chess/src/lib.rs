//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

#[macro_use]
mod macros;

mod game;
mod model;

pub use game::{
    DrawClaim, DrawClaims, DrawReason, ForceMoveError, ForcedMove, Game, GameStatus, GameSyncError,
    HistoryError, InvalidPly, MoveCount, MoveError, MoveHash, MoveHistory, MoveHistoryIter, MoveStep,
    Ply,
};
pub use model::{
    AllSquares, Board, BoardDirection, BoardEdge, BoardPieces, CastlingRights, ChessMove, Color,
    File, FileOffset, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber, InvalidPromotion,
    InvalidSquare, ParseMoveError, ParseSquareError, Piece, PieceKind, Rank, RankOffset, Square,
    SquareCount, SquareIndex, SquareOffset, SquareRay, SquareSet, SquareSetSquares,
};
