//! Piece-specific destination and attack calculators.

mod bishop;
mod king;
mod knight;
mod pawn;
mod queen;
mod rook;
mod shared;

use crate::{Board, Color, Piece, PieceKind, Square, SquareSet};

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

pub(super) fn is_attacked(board: &Board, square: Square, by: Color) -> bool {
    board
        .iter()
        .filter(|piece| piece.color() == by)
        .any(|piece| attacks(board, piece).contains(square))
}
