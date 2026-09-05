//! The game aggregate and its immutable public state views.

mod history_state;
mod logging;
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
    ///
    /// The authoritative [`GameHistory`] is anchored to [`Board::INITIAL`],
    /// so [`Game::verify`] and [`Game::rebuild_board`] replay from the
    /// standard position. Creation is reported through the `chess::game`
    /// log target; see [`Game::accept`](crate::Game::accept) for how peer
    /// steps join this history.
    #[must_use]
    pub fn new() -> Self {
        Self::from_board(Board::INITIAL)
    }

    /// Creates a game from a board with an anchored authoritative history.
    ///
    /// The supplied board becomes both the replay base remembered as the
    /// initial board and the starting board cache. The new [`GameHistory`]
    /// is anchored to it via [`GameHistory::for_board`](crate::GameHistory::for_board),
    /// so later [`Game::verify`] calls confirm the cache still reproduces
    /// that history. Terminal positions are sealed immediately with a final
    /// event, and creation is logged on the `chess::game` target.
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
    /// The board is a derived cache of the authoritative [`GameHistory`];
    /// every accepted move updates it, while invalid and final events leave
    /// piece placement untouched. Use [`Game::rebuild_board`] to replay the
    /// history independently and [`Game::verify`] to confirm the cache has
    /// not diverged.
    #[must_use]
    pub const fn board(&self) -> &Board {
        &self.board
    }

    /// Returns the board that anchors history replay.
    ///
    /// [`Game::rebuild_board`] replays accepted [`HistoryEvent::Move`](crate::HistoryEvent::Move)
    /// events from this board, and [`Game::verify`] compares that replay
    /// against the cached [`Game::board`].
    pub(super) const fn initial_board(&self) -> Board {
        self.initial_board
    }

    /// Returns the piece currently occupying `square`.
    ///
    /// This reads the derived board cache; the authoritative answer for
    /// audit purposes is the [`GameHistory`] returned by [`Game::history`].
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.board.piece_at(square)
    }

    /// Returns the immutable, hash-linked authoritative history.
    ///
    /// The history is the source of truth: [`Game::board`] is only a cache
    /// of replaying its move events. An invalid tip blocks valid
    /// transitions until [`Game::resolve_latest_invalid`] clears it
    /// newest-first, and a final tip seals the timeline permanently.
    #[must_use]
    pub const fn history(&self) -> &GameHistory {
        &self.history
    }

    /// Returns every legal move while history accepts valid transitions.
    ///
    /// The returned iterator is empty while an invalid event blocks play
    /// or a final event has sealed history; both states are reported by
    /// [`Game::status`](crate::Game::status). Otherwise it yields the legal
    /// moves of the cached [`Game::board`].
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
