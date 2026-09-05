//! Detection of material combinations in which checkmate is impossible.

use crate::{Board, Color, PieceKind, Square};

/// Returns whether the material makes checkmate impossible by any legal sequence.
///
/// Any pawn, rook, or queen retains mating potential. Otherwise only
/// bare kings, a single minor piece, or same-square-color bishops (with no
/// knights) count as insufficient; opposite-color bishops can still mate.
/// Both sides must retain exactly one king. Used for automatic draws via
/// [`crate::Game::status`](crate::Game::status), never as a claim.
pub(super) fn is_insufficient(board: &Board) -> bool {
    let mut kings = [0_u8; 2];
    let mut minor_count = 0_u8;
    let mut knight_count = 0_u8;
    let mut bishop_color = None;

    for square in Square::all() {
        let Some(piece) = board.piece_at(square) else {
            continue;
        };
        match piece.kind() {
            PieceKind::King => kings[color_index(piece.color())] += 1,
            PieceKind::Pawn | PieceKind::Rook | PieceKind::Queen => return false,
            PieceKind::Knight => {
                minor_count = minor_count.saturating_add(1);
                knight_count = knight_count.saturating_add(1);
            }
            PieceKind::Bishop => {
                minor_count = minor_count.saturating_add(1);
                let index = piece.square().index().value();
                let color = ((index % 8) + (index / 8)) % 2;
                if bishop_color.is_some_and(|existing| existing != color) {
                    return false;
                }
                bishop_color = Some(color);
            }
        }
    }

    kings == [1, 1] && (minor_count <= 1 || (knight_count == 0 && bishop_color.is_some()))
}

const fn color_index(color: Color) -> usize {
    match color {
        Color::White => 0,
        Color::Black => 1,
    }
}
