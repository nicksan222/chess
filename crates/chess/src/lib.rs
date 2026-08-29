//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

mod model;

pub use model::{
    AllSquares, BitBoard, BitBoardSquares, BoardDirection, BoardEdge, ChessMove, Color,
    InvalidPromotion, InvalidSquare, Piece, PieceKind, Square, SquareRay,
};
