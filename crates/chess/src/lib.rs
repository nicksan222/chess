//! Integration-neutral chess-domain types and logic.

#![no_std]
#![forbid(unsafe_code)]

mod bitboard;
mod square;

pub use bitboard::{BitBoard, Squares as BitBoardSquares};
pub use square::{AllSquares, InvalidSquare, Square};
