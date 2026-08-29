//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

mod model;

pub use model::{
    AllSquares, BoardDirection, BoardEdge, ChessMove, Color, File, InvalidPromotion, InvalidSquare,
    Piece, PieceKind, Rank, Square, SquareCount, SquareIndex, SquareOffset, SquareRay, SquareSet,
    SquareSetSquares,
};
