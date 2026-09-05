//! Legal move generation and king-safety filtering.

use crate::{Board, ChessMove, Color, Piece, PieceKind, SquareSet};

use super::calculators;

impl Board {
    /// Returns every legal destination for `piece` in this board.
    ///
    /// The piece-specific calculator supplies candidate squares. This final
    /// layer removes king captures and moves that leave the moving king in
    /// check. Promotion choices all share one destination square.
    ///
    /// Returns [`SquareSet::EMPTY`] when `piece` is absent, stale, or belongs
    /// to the side not to move. Every returned square is king-safe; combine
    /// with [`Piece::legal_moves`](crate::Piece::legal_moves) to expand pawn
    /// promotions into one [`ChessMove`] per promotion kind. See also
    /// [`Board::legal_moves`].
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
    ///
    /// Only fully legal, king-safe moves are yielded: each piece contributes
    /// its [`Board::legal_destinations`] filtered set, so pseudo-legal moves
    /// that expose the king are excluded. The iterator is empty when it is
    /// checkmate or stalemate; use [`Board::is_in_check`] to distinguish them.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::Board;
    ///
    /// let board = Board::INITIAL;
    /// assert_eq!(board.legal_moves().count(), 20);
    /// ```
    pub fn legal_moves(&self) -> impl Iterator<Item = ChessMove> + '_ {
        let side = self.side_to_move();
        self.pieces()
            .filter(move |piece| piece.color() == side)
            .flat_map(|piece| piece.legal_moves(self))
    }

    /// Returns whether `color`'s king is currently attacked.
    ///
    /// Attackers are computed with piece attack maps against the king square,
    /// independent of whose turn it is. A missing king reports `false` rather
    /// than panicking. Used by legality filtering and by
    /// [`crate::Game::status`](crate::Game::status) derivation.
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
