//! Rook destinations and attacked-square calculation.

use crate::{Board, Piece, SquareSet};

use super::shared;

/// Orthogonal sliding candidates that stop at the first blocker.
///
/// Pseudo-legal only; king safety is filtered later by
/// [`Board::legal_destinations`](crate::Board::legal_destinations).
pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_destinations(board, piece, &shared::ORTHOGONALS)
}

/// Orthogonal sliding attacks through the first occupied square.
///
/// Used by check detection; see [`super::is_attacked`].
pub(super) fn attacks(board: &Board, piece: Piece) -> SquareSet {
    shared::ray_attacks(board, piece, &shared::ORTHOGONALS)
}
