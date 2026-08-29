//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

mod model;
pub mod notation;

pub use model::{
    AllSquares, BitBoard, BitBoardSquares, Color, InvalidSquare, Piece, PieceKind, Square,
};
