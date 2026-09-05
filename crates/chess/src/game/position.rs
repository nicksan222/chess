//! Read-only game position queries.

use crate::{BoardPieces, Color, Game, Piece};

impl Game {
    /// Returns self-locating pieces in board order.
    ///
    /// Reads the derived board cache; the authoritative [`GameHistory`](crate::GameHistory)
    /// behind it is available from [`Game::history`](crate::Game::history).
    /// While an invalid event blocks play or a final event seals history,
    /// the pieces reflect the position at which play stopped.
    pub fn pieces(&self) -> BoardPieces<'_> {
        self.board().pieces()
    }

    /// Returns the player whose turn it is.
    ///
    /// Read from the board cache, which [`Game::verify`](crate::Game::verify)
    /// confirms still reproduces the authoritative [`GameHistory`](crate::GameHistory).
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.board().side_to_move()
    }

    /// Returns whether the side to move is currently in check.
    ///
    /// Evaluates the cached [`Game::board`](crate::Game::board) for the
    /// side to move. Checkmate derived from this query seals history with
    /// a final event via local play and accepted peer moves.
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
