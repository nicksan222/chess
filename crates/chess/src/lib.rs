//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

mod game;
mod model;

pub use model::{
    AllSquares, Board, BoardDirection, BoardEdge, BoardPieces, CastlingRights, ChessMove, Color,
    File, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber, InvalidPromotion, InvalidSquare,
    Piece, PieceKind, Rank, Square, SquareCount, SquareIndex, SquareOffset, SquareRay, SquareSet,
    SquareSetSquares,
};
