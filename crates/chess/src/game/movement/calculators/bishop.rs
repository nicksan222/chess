//! Bishop destinations and attacked-square calculation.

use crate::{Board, Piece, SquareSet};

use super::shared;

pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_destinations(board, piece, &shared::DIAGONALS)
}

pub(super) fn attacks(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_attacks(board, piece, &shared::DIAGONALS)
}
