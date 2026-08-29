use crate::{Board, Piece, SquareOffset, SquareSet};

use super::shared;

const OFFSETS: [SquareOffset; 8] = [
    SquareOffset::new(1, 2),
    SquareOffset::new(2, 1),
    SquareOffset::new(2, -1),
    SquareOffset::new(1, -2),
    SquareOffset::new(-1, -2),
    SquareOffset::new(-2, -1),
    SquareOffset::new(-2, 1),
    SquareOffset::new(-1, 2),
];

pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::offset_destinations(board, piece, &OFFSETS)
}

pub(super) fn attacks(piece: Piece) -> SquareSet {
    shared::offset_attacks(piece, &OFFSETS)
}
