//! Detection of material combinations in which checkmate is impossible.

use crate::{Board, PieceKind, Square};

/// Returns whether the material makes checkmate impossible by any legal sequence.
///
/// Any pawn, rook, or queen retains mating potential. Otherwise only
/// bare kings, a single minor piece, or same-square-color bishops (with no
/// knights) count as insufficient; opposite-color bishops can still mate.
/// Both sides must retain exactly one king. Used for automatic draws via
/// [`crate::Game::status`](crate::Game::status), never as a claim.
pub(super) fn is_insufficient(board: &Board) -> bool {
    MaterialSummary::of(board).is_insufficient()
}

/// Counts of the material that decides whether checkmate is still possible.
#[derive(Default)]
struct MaterialSummary {
    kings: [u8; 2],
    knights: u8,
    bishops: u8,
    light_bishops: u8,
    dark_bishops: u8,
    /// Whether any pawn, rook, or queen is on the board.
    has_major_material: bool,
}

impl MaterialSummary {
    fn of(board: &Board) -> Self {
        let mut summary = Self::default();
        for square in Square::all() {
            let Some(piece) = board.piece_at(square) else {
                continue;
            };
            match piece.kind() {
                PieceKind::King => summary.kings[piece.color().index()] += 1,
                PieceKind::Pawn | PieceKind::Rook | PieceKind::Queen => {
                    summary.has_major_material = true;
                }
                PieceKind::Knight => summary.knights = summary.knights.saturating_add(1),
                PieceKind::Bishop => {
                    summary.bishops = summary.bishops.saturating_add(1);
                    if square.is_light() {
                        summary.light_bishops = summary.light_bishops.saturating_add(1);
                    } else {
                        summary.dark_bishops = summary.dark_bishops.saturating_add(1);
                    }
                }
            }
        }
        summary
    }

    fn minor_pieces(&self) -> u8 {
        self.knights.saturating_add(self.bishops)
    }

    /// Whether every bishop stands on one square color.
    fn bishops_share_color(&self) -> bool {
        self.light_bishops == 0 || self.dark_bishops == 0
    }

    fn is_insufficient(&self) -> bool {
        let one_king_each = self.kings == [1, 1];
        let at_most_one_minor = self.minor_pieces() <= 1;
        let only_same_color_bishops =
            self.knights == 0 && self.bishops > 0 && self.bishops_share_color();
        one_king_each && !self.has_major_material && (at_most_one_minor || only_same_color_bishops)
    }
}
