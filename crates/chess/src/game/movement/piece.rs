//! Piece-oriented legal move queries and move commands.

use crate::{Board, ChessMove, Game, HistoryStep, MoveError, Piece, PieceKind, Square, SquareSet};

use super::transition::is_back_rank;

impl Piece {
    /// Returns every currently legal destination for this piece.
    #[must_use]
    pub fn legal_destinations(self, board: &Board) -> SquareSet {
        board.legal_destinations(self)
    }

    /// Returns every currently legal move for this piece.
    ///
    /// Pawn promotions produce one move for each valid promotion kind.
    pub fn legal_moves(self, board: &Board) -> impl Iterator<Item = ChessMove> {
        self.legal_destinations(board)
            .into_iter()
            .flat_map(move |destination| self.moves_to(destination).into_iter().flatten())
    }

    /// Moves this piece in `game`, recording the resulting hash-linked step.
    ///
    /// Pawn moves to the back rank promote to a queen. Use
    /// [`Piece::move_and_promote`] to select another promotion kind.
    pub fn move_to(self, destination: Square, game: &mut Game) -> Result<HistoryStep, MoveError> {
        game.move_piece(self, destination, None)
    }

    /// Moves and promotes this pawn in `game`, recording the resulting step.
    pub fn move_and_promote(
        self,
        destination: Square,
        promotion: PieceKind,
        game: &mut Game,
    ) -> Result<HistoryStep, MoveError> {
        game.move_piece(self, destination, Some(promotion))
    }

    fn moves_to(self, destination: Square) -> [Option<ChessMove>; 4] {
        if self.kind() == PieceKind::Pawn && is_back_rank(destination, self.color()) {
            PieceKind::PROMOTIONS
                .map(|kind| ChessMove::promotion(self.square(), destination, kind).ok())
        } else {
            [
                Some(ChessMove::new(self.square(), destination)),
                None,
                None,
                None,
            ]
        }
    }
}
