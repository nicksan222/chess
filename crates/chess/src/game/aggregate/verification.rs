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
