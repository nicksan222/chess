//! Queen destinations and attacked-square calculation.

use crate::{Board, Piece, SquareSet};

use super::shared;

/// Diagonal plus orthogonal sliding candidates for the queen.
///
/// Pseudo-legal only; king safety is filtered later by
/// [`Board::legal_destinations`](crate::Board::legal_destinations).
pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_destinations(board, piece, &shared::DIAGONALS)
        | shared::ray_destinations(board, piece, &shared::ORTHOGONALS)
}

/// Diagonal plus orthogonal sliding attacks for check detection.
///
/// See [`super::is_attacked`].
pub(super) fn attacks(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_attacks(board, piece, &shared::DIAGONALS)
        | shared::ray_attacks(board, piece, &shared::ORTHOGONALS)
}
