//! The game aggregate and its immutable public state views.

mod history_state;
mod play;
mod sync;
mod verification;

use crate::{Board, ChessMove, Piece, Square};

use super::GameHistory;

pub use verification::GameVerificationError;

/// A playable board whose authoritative state transitions live in one history.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Game {
    initial_board: Board,
    board: Board,
    history: GameHistory,
}

impl Game {
    /// Creates a game in the standard initial board.
    #[must_use]
    pub fn new() -> Self {
        Self::from_board(Board::INITIAL)
    }

    /// Creates a game from a board with an anchored authoritative history.
    #[must_use]
    pub fn from_board(board: Board) -> Self {
        let mut game = Self {
            initial_board: board,
            board,
            history: GameHistory::for_board(&board),
        };
        game.finalize_if_terminal();
        game
    }

    /// Returns the current board cache.
    #[must_use]
    pub const fn board(&self) -> &Board {
        &self.board
    }

    pub(super) const fn initial_board(&self) -> Board {
        self.initial_board
    }

    /// Returns the piece currently occupying `square`.
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.board.piece_at(square)
    }

    /// Returns the immutable, hash-linked authoritative history.
    #[must_use]
    pub const fn history(&self) -> &GameHistory {
        &self.history
    }

    /// Returns every legal move while history accepts valid transitions.
    pub fn legal_moves(&self) -> impl Iterator<Item = ChessMove> + '_ {
        self.accepts_moves()
            .then(|| self.board.legal_moves())
            .into_iter()
            .flatten()
    }
}

impl Default for Game {
    fn default() -> Self {
        Self::new()
    }
}
