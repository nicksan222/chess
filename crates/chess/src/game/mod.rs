//! The playable game aggregate and its lifecycle views.

mod history_state;
mod logging;
mod play;
mod position;
mod status;
mod sync;
mod verification;

use crate::{Board, ChessMove, GameHistory, Piece, Square};

pub use status::{DrawClaim, DrawClaims, DrawReason, GameStatus};
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
    ///
    /// The returned [`Game`] starts from [`Board::INITIAL`], anchors an empty
    /// [`GameHistory`] to that board, and immediately evaluates whether the
    /// position is terminal. Standard initial placement is active, so the
    /// history remains empty and White is the side to move.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Board, Game};
    ///
    /// let game = Game::new();
    /// assert_eq!(game.board(), &Board::INITIAL);
    /// assert!(game.history().is_empty());
    /// ```
    #[must_use]
    pub fn new() -> Self {
        Self::from_board(Board::INITIAL)
    }

    /// Creates a game from a board with an anchored authoritative history.
    ///
    /// The supplied [`Board`] becomes both the immutable replay origin and the
    /// initial derived board cache. The new empty [`GameHistory`] is anchored
    /// to the complete position, preventing equal move streams from different
    /// starting boards from synchronizing. The position is immediately
    /// adjudicated; checkmate, stalemate, or an automatic draw appends a final
    /// event before this function returns.
    ///
    /// This constructor accepts composed positions as-is. Callers constructing
    /// setup or reconciliation boards are responsible for choosing coherent
    /// piece placement and metadata before creating the game.
    #[must_use]
    pub fn from_board(board: Board) -> Self {
        let mut game = Self {
            initial_board: board,
            board,
            history: GameHistory::for_board(&board),
        };
        game.log_created();
        game.finalize_if_terminal();
        game
    }

    /// Returns the current board cache.
    ///
    /// The returned [`Board`] is the efficient position used for move queries;
    /// accepted move events in [`Game::history`] remain authoritative.
    /// [`Game::rebuild_board`] can independently reproduce this cache from the
    /// initial board and retained move events, while [`Game::verify`] checks
    /// that both representations agree.
    #[must_use]
    pub const fn board(&self) -> &Board {
        &self.board
    }

    /// Returns the immutable board from which history replay begins.
    ///
    /// Unlike [`Game::board`], this value never advances after accepted moves.
    /// Replay, verification, and the history anchor all rely on this exact
    /// starting position.
    pub(super) const fn initial_board(&self) -> Board {
        self.initial_board
    }

    /// Returns the piece currently occupying `square`.
    ///
    /// This reads the derived current-board cache and returns the self-locating
    /// [`Piece`] stored at `square`, or `None` when the square is empty. It does
    /// not inspect or mutate authoritative history.
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.board.piece_at(square)
    }

    /// Returns the immutable, hash-linked authoritative history.
    ///
    /// The history contains every accepted move, unresolved invalid operation,
    /// and terminal result. Callers may inspect or transport its steps, but
    /// game mutation remains centralized through methods such as [`Game::play`]
    /// and [`Game::accept`].
    #[must_use]
    pub const fn history(&self) -> &GameHistory {
        &self.history
    }

    /// Returns every legal move while history accepts valid transitions.
    ///
    /// An active game delegates to [`Board::legal_moves`] on the current cache.
    /// If the newest history event is invalid or final, this iterator is empty
    /// even when the underlying board position itself has legal chess moves.
    /// Resolve invalid events newest-first before querying playable moves again.
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
