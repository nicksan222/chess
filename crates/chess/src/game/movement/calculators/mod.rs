//! Piece-specific destination and attack calculators.

mod bishop;
mod king;
mod knight;
mod pawn;
mod queen;
mod rook;
mod shared;

use crate::{Board, Color, Piece, PieceKind, Square, SquareSet};

/// Dispatches pseudo-legal candidate destinations by piece kind.
///
/// These candidates ignore king safety; [`Board::legal_destinations`] filters
/// them into fully legal squares. King captures are also removed there.
pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    match piece.kind() {
        PieceKind::Pawn => pawn::destinations(board, piece),
        PieceKind::Knight => knight::destinations(board, piece),
        PieceKind::Bishop => bishop::destinations(board, piece),
        PieceKind::Rook => rook::destinations(board, piece),
        PieceKind::Queen => queen::destinations(board, piece),
        PieceKind::King => king::destinations(board, piece),
    }
}

/// Returns the attack map for `piece`, ignoring king safety.
///
/// Unlike [`destinations`], blockers still bound sliding rays but occupancy
/// by either color counts as attacked. Used by [`is_attacked`] and
/// [`Board::is_in_check`](crate::Board::is_in_check).
pub(super) fn attacks(board: &Board, piece: Piece) -> SquareSet {
    match piece.kind() {
        PieceKind::Pawn => pawn::attacks(piece),
        PieceKind::Knight => knight::attacks(piece),
        PieceKind::Bishop => bishop::attacks(board, piece),
        PieceKind::Rook => rook::attacks(board, piece),
        PieceKind::Queen => queen::attacks(board, piece),
        PieceKind::King => king::attacks(piece),
    }
}

/// Returns whether `square` is attacked by any piece of color `by`.
///
/// Tests every attacker of color `by` with its attack map, so pins and king
/// safety are ignored. Board legality layers use this for check detection
/// and castling-path validation.
pub(super) fn is_attacked(board: &Board, square: Square, by: Color) -> bool {
    board
        .iter()
        .filter(|piece| piece.color() == by)
        .any(|piece| attacks(board, piece).contains(square))
}
