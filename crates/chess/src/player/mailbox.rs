//! Shared one-move mailbox for externally supplied player input.

use core::fmt;

use crate::ChessMove;

use super::PlayerResponse;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(super) struct MoveMailbox {
    pending: Option<ChessMove>,
}

impl MoveMailbox {
    /// Creates an empty mailbox holding no pending move.
    ///
    /// The mailbox backs non-blocking [`Player`](super::Player) polling:
    /// an empty mailbox polls as pending rather than waiting for input.
    pub(super) const fn new() -> Self {
        Self { pending: None }
    }

    /// Stages `chess_move` when no move is currently staged.
    ///
    /// Enforces the single-pending discipline: at most one externally
    /// supplied move waits for the next poll. Withdraw it with
    /// [`cancel`](Self::cancel) or consume it with [`poll`](Self::poll)
    /// before submitting again.
    ///
    /// # Errors
    ///
    /// Returns [`SubmitError::MovePending`] carrying the still-staged move
    /// when the mailbox is already full.
    pub(super) fn submit(&mut self, chess_move: ChessMove) -> Result<(), SubmitError> {
        if let Some(pending) = self.pending {
            return Err(SubmitError::MovePending(pending));
        }
        self.pending = Some(chess_move);
        Ok(())
    }

    /// Returns the staged move without consuming it, if any.
    ///
    /// Peeking leaves the single-pending slot occupied; only
    /// [`cancel`](Self::cancel) or [`poll`](Self::poll) frees it.
    pub(super) const fn pending(&self) -> Option<ChessMove> {
        self.pending
    }

    /// Withdraws and returns the staged move, if any.
    ///
    /// Frees the single-pending slot so a replacement move can be
    /// submitted before the next non-blocking [`poll`](Self::poll).
    pub(super) fn cancel(&mut self) -> Option<ChessMove> {
        self.pending.take()
    }

    /// Consumes the staged move, or reports pending without blocking.
    ///
    /// Never waits for input: yields [`PlayerResponse::Move`] when a move
    /// was submitted and [`PlayerResponse::Pending`] otherwise. The session
    /// validates consumed moves against the authoritative game before
    /// committing them.
    pub(super) fn poll(&mut self) -> PlayerResponse {
        match self.pending.take() {
            Some(chess_move) => PlayerResponse::Move(chess_move),
            None => PlayerResponse::Pending,
        }
    }
}

/// A move cannot be submitted to a player.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SubmitError {
    /// Computer players produce their own moves.
    ComputerControlled,
    /// A previously submitted move has not been processed.
    MovePending(ChessMove),
}

impl fmt::Display for SubmitError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ComputerControlled => {
                formatter.write_str("a move cannot be submitted to a computer player")
            }
            Self::MovePending(chess_move) => {
                write!(formatter, "move {chess_move} is still pending")
            }
        }
    }
}

impl core::error::Error for SubmitError {}
