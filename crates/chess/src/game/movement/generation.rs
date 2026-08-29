use crate::{Board, Color, Piece, PieceKind, SquareSet};

use super::calculators;

impl Board {
    /// Returns every legal destination for `piece` in this board.
    ///
    /// The piece-specific calculator supplies candidate squares. This final
    /// layer removes king captures and moves that leave the moving king in
    /// check. Promotion choices all share one destination square.
    #[must_use]
    pub fn destinations(&self, piece: Piece) -> SquareSet {
        if self.piece_at(piece.square()) != Some(piece) || piece.color() != self.side_to_move() {
            return SquareSet::EMPTY;
        }

        let mut candidates = calculators::destinations(self, piece);
        for destination in candidates {
            if self
                .piece_at(destination)
                .is_some_and(|target| target.kind() == PieceKind::King)
            {
                candidates.remove(destination);
            }
        }
        candidates
            .into_iter()
            .filter(|destination| {
                let mut next = *self;
                next.apply_unchecked(piece, *destination, None);
                !next.is_in_check(piece.color())
            })
            .collect()
    }

    /// Returns whether `color`'s king is currently attacked.
    #[must_use]
    pub fn is_in_check(&self, color: Color) -> bool {
        let Some(king) = self
            .iter()
            .find(|piece| piece.color() == color && piece.kind() == PieceKind::King)
        else {
            return false;
        };
        calculators::is_attacked(self, king.square(), color.opposite())
    }
}
