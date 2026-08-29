use crate::{ChessMove, Game, MoveError, MoveStep};

impl ChessMove {
    /// Plays this move on `game`, recording the resulting hash-linked step.
    pub fn play(self, game: &mut Game) -> Result<MoveStep, MoveError> {
        game.play(self)
    }
}
