//! Convenience methods for playing owned move values.

use crate::{ChessMove, Game, HistoryStep, MoveError};

impl ChessMove {
    /// Plays this move on `game`, recording the resulting hash-linked step.
    ///
    /// This is the owned-value entry point for `make_move` semantics:
    /// legality, king safety, and promotion canonicalization are enforced by
    /// [`Board`](crate::Board) validation, and [`Game`](crate::Game) appends
    /// the canonical move plus any terminal event to authoritative history.
    /// Prefer [`Game::play`](crate::Game::play) when the move is borrowed.
    ///
    /// # Errors
    ///
    /// Returns [`MoveError`](crate::MoveError) when the game is over, an
    /// invalid event is pending, the origin is empty, the side is wrong, the
    /// destination is illegal, or the promotion is unexpected or invalid.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Game, Square};
    ///
    /// let mut game = Game::new();
    /// let step = ChessMove::new(Square::E2, Square::E4).play(&mut game)?;
    /// assert!(game.board().piece_at(Square::E4).is_some());
    /// assert!(game.board().piece_at(Square::E2).is_none());
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn play(self, game: &mut Game) -> Result<HistoryStep, MoveError> {
        game.play(self)
    }
}
