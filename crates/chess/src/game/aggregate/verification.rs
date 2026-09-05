//! Replay and consistency checks for the derived board cache.

use core::fmt;

use crate::{Board, FinalState, HistoryError, HistoryEvent, MoveError, Ply};

use super::Game;

/// A game history could not reproduce the cached game state.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum GameVerificationError {
    /// The history's sequence or hash chain is invalid.
    History(HistoryError),
    /// A retained move is not legal when replayed from the initial board.
    Replay {
        /// The sequence number of the invalid move event.
        ply: Ply,
        /// The move failure encountered during replay.
        error: MoveError,
    },
    /// Replayed moves do not produce the board cache held by [`Game`].
    BoardCache,
    /// The retained final event is not valid for the reproduced position.
    FinalState {
        /// The unsupported terminal result.
        final_state: FinalState,
    },
}

impl fmt::Display for GameVerificationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::History(error) => write!(formatter, "history validation failed: {error}"),
            Self::Replay { ply, error } => {
                write!(formatter, "history event {ply} cannot be replayed: {error}")
            }
            Self::BoardCache => {
                formatter.write_str("authoritative history does not reproduce the board cache")
            }
            Self::FinalState { .. } => {
                formatter.write_str("the final history event is not valid for the position")
            }
        }
    }
}

impl core::error::Error for GameVerificationError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::History(error) => Some(error),
            Self::Replay { error, .. } => Some(error),
            Self::BoardCache | Self::FinalState { .. } => None,
        }
    }
}

impl Game {
    /// Replays accepted move events from the initial board.
    ///
    /// Invalid and final events do not mutate piece placement and are skipped.
    /// This method is useful when loading persistence or diagnosing a cache
    /// mismatch without trusting the board currently held by the game.
    ///
    /// Replay starts from the anchored initial board and applies every
    /// retained [`HistoryEvent::Move`](crate::HistoryEvent) in order, so
    /// the result must equal the [`Game::board`] cache whenever history and
    /// cache agree. [`Game::verify`] uses this comparison to detect
    /// divergence between the authoritative [`GameHistory`](crate::GameHistory)
    /// and its cache.
    ///
    /// # Errors
    ///
    /// Returns [`GameVerificationError::Replay`](crate::GameVerificationError::Replay)
    /// naming the ply and [`MoveError`](crate::MoveError) when a retained
    /// move is no longer legal from the replayed position.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Game, Square};
    ///
    /// let mut game = Game::new();
    /// game.play(ChessMove::new(Square::E2, Square::E4))?;
    /// assert_eq!(game.rebuild_board()?, *game.board());
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn rebuild_board(&self) -> Result<Board, GameVerificationError> {
        let mut board = self.initial_board;
        for step in self.history.iter() {
            let HistoryEvent::Move(chess_move) = step.event() else {
                continue;
            };
            board
                .make_move(chess_move)
                .map_err(|error| GameVerificationError::Replay {
                    ply: step.ply(),
                    error,
                })?;
        }
        Ok(board)
    }

    /// Verifies hashes, replayed board state, and any terminal event.
    ///
    /// Successful verification establishes that the board is only a cache of
    /// the authoritative linked history and has not diverged from it.
    ///
    /// Checks run in layers: the [`GameHistory`](crate::GameHistory) hash
    /// chain and tip, then [`Game::rebuild_board`] equality with the cached
    /// [`Game::board`](crate::Game::board), and finally semantic
    /// availability of a retained final event for the replayed position.
    /// Verification is read-only; it neither mutates history nor repairs
    /// the cache.
    ///
    /// # Errors
    ///
    /// Returns [`GameVerificationError::History`](crate::GameVerificationError::History)
    /// for a broken sequence or hash link,
    /// [`GameVerificationError::BoardCache`](crate::GameVerificationError::BoardCache)
    /// when replayed moves do not reproduce the cache,
    /// [`GameVerificationError::Replay`](crate::GameVerificationError::Replay)
    /// when a retained move fails replay, and
    /// [`GameVerificationError::FinalState`](crate::GameVerificationError::FinalState)
    /// when the retained terminal result is not valid for the position.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Game, Square};
    ///
    /// let mut game = Game::new();
    /// game.play(ChessMove::new(Square::E2, Square::E4))?;
    /// game.play(ChessMove::new(Square::E7, Square::E5))?;
    /// game.verify()?;
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn verify(&self) -> Result<(), GameVerificationError> {
        self.history
            .verify()
            .map_err(GameVerificationError::History)?;
        if self.rebuild_board()? != self.board {
            return Err(GameVerificationError::BoardCache);
        }
        if let Some(HistoryEvent::Final(final_state)) =
            self.history.latest().map(|step| step.event())
            && !self.final_state_is_available(final_state)
        {
            return Err(GameVerificationError::FinalState { final_state });
        }
        Ok(())
    }
}
