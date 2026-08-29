use crate::{Board, ChessMove, Color, Piece, PieceKind, Square, SquareSet};

use super::{calculators, transition::is_back_rank};

impl Board {
    /// Returns every legal destination for `piece` in this board.
    ///
    /// The piece-specific calculator supplies candidate squares. This final
    /// layer removes king captures and moves that leave the moving king in
    /// check. Promotion choices all share one destination square.
    #[must_use]
    pub fn legal_destinations(&self, piece: Piece) -> SquareSet {
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

    /// Returns every legal move for the side to move.
    ///
    /// Pawn promotions produce one move for each valid promotion kind.
    pub fn legal_moves(&self) -> impl Iterator<Item = ChessMove> + '_ {
        let side = self.side_to_move();
        self.pieces()
            .filter(move |piece| piece.color() == side)
            .flat_map(move |piece| {
                self.legal_destinations(piece)
                    .into_iter()
                    .flat_map(move |destination| moves_to(piece, destination).into_iter().flatten())
            })
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

fn moves_to(piece: Piece, destination: Square) -> [Option<ChessMove>; 4] {
    if piece.kind() == PieceKind::Pawn && is_back_rank(destination, piece.color()) {
        [
            PieceKind::Knight,
            PieceKind::Bishop,
            PieceKind::Rook,
            PieceKind::Queen,
        ]
        .map(|kind| ChessMove::promotion(piece.square(), destination, kind).ok())
    } else {
        [
            Some(ChessMove::new(piece.square(), destination)),
            None,
            None,
            None,
        ]
    }
}
