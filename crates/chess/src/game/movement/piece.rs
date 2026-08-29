use crate::{Board, Game, MoveError, MoveStep, Piece, PieceKind, Square, SquareSet};

impl Piece {
    /// Returns every currently legal destination for this piece.
    #[must_use]
    pub fn where_can_move(self, board: &Board) -> SquareSet {
        board.destinations(self)
    }

    /// Moves this piece in `game`, recording the resulting hash-linked step.
    ///
    /// Pawn moves to the back rank promote to a queen. Use
    /// [`Piece::move_and_promote`] to select another promotion kind.
    pub fn move_to(self, destination: Square, game: &mut Game) -> Result<MoveStep, MoveError> {
        game.move_piece(self, destination, None)
    }

    /// Moves and promotes this pawn in `game`, recording the resulting step.
    pub fn move_and_promote(
        self,
        destination: Square,
        promotion: PieceKind,
        game: &mut Game,
    ) -> Result<MoveStep, MoveError> {
        game.move_piece(self, destination, Some(promotion))
    }
}
