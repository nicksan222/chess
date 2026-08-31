//! Read-only game position queries.

use crate::{BoardPieces, Color, Game, Piece};

impl Game {
    /// Returns self-locating pieces in board order.
    pub fn pieces(&self) -> BoardPieces<'_> {
        self.board().pieces()
    }

    /// Returns the player whose turn it is.
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.board().side_to_move()
    }

    /// Returns whether the side to move is currently in check.
    #[must_use]
    pub fn is_in_check(&self) -> bool {
        self.board().is_in_check(self.board().side_to_move())
    }
}

impl<'a> IntoIterator for &'a Game {
    type Item = Piece;
    type IntoIter = BoardPieces<'a>;

    fn into_iter(self) -> Self::IntoIter {
        self.pieces()
    }
}
