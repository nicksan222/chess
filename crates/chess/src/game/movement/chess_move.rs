use crate::{ChessMove, Game, HistoryStep, MoveError};

impl ChessMove {
    /// Plays this move on `game`, recording the resulting hash-linked step.
    pub fn play(self, game: &mut Game) -> Result<HistoryStep, MoveError> {
        game.play(self)
    }
}
