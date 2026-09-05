//! King movement, attacks, and castling calculation.

use crate::{Board, Color, Piece, PieceKind, Square, SquareSet};

use super::{is_attacked, shared};

/// King steps plus validated castling destinations.
///
/// Castling requires the king on its home square, intact rights, a matching
/// rook, empty transit squares, and no attack on the king or transit squares.
/// Final king safety is still filtered by
/// [`Board::legal_destinations`](crate::Board::legal_destinations).
pub(super) fn destinations(board: &Board, king: Piece) -> SquareSet {
    shared::offset_destinations(board, king, &shared::KING_OFFSETS)
        | castling_destinations(board, king)
}

/// King attack squares, regardless of occupancy or check.
///
/// Used by check detection; moving into attack is rejected later during
/// legality filtering.
pub(super) fn attacks(king: Piece) -> SquareSet {
    shared::offset_attacks(king, &shared::KING_OFFSETS)
}

fn castling_destinations(board: &Board, king: Piece) -> SquareSet {
    let (home, kingside_rook, queenside_rook, kingside_path, queenside_path) = match king.color() {
        Color::White => (
            Square::E1,
            Square::H1,
            Square::A1,
            [Square::F1, Square::G1],
            [Square::D1, Square::C1, Square::B1],
        ),
        Color::Black => (
            Square::E8,
            Square::H8,
            Square::A8,
            [Square::F8, Square::G8],
            [Square::D8, Square::C8, Square::B8],
        ),
    };
    let opponent = king.color().opposite();
    if king.square() != home || is_attacked(board, home, opponent) {
        return SquareSet::EMPTY;
    }

    let mut destinations = SquareSet::EMPTY;
    let rights = board.castling_rights();
    let rook_matches =
        |square| board.piece_at(square) == Some(Piece::new(king.color(), PieceKind::Rook, square));
    if rights.kingside(king.color())
        && rook_matches(kingside_rook)
        && kingside_path
            .iter()
            .all(|square| board.piece_at(*square).is_none())
        && kingside_path
            .iter()
            .all(|square| !is_attacked(board, *square, opponent))
    {
        destinations.insert(kingside_path[1]);
    }
    if rights.queenside(king.color())
        && rook_matches(queenside_rook)
        && queenside_path
            .iter()
            .all(|square| board.piece_at(*square).is_none())
        && queenside_path[..2]
            .iter()
            .all(|square| !is_attacked(board, *square, opponent))
    {
        destinations.insert(queenside_path[1]);
    }
    destinations
}
