//! Shared externally supplied move source.
//!
//! Human and online players currently share mailbox semantics: an external
//! observer submits at most one pending move, polling takes it, and nothing
//! ever blocks waiting for input. The two player kinds stay distinct so local
//! observation (human UI, board sensors) and transport-fed play (network peer)
//! can diverge later with transport, authentication, or timeout metadata
//! without changing the public [`crate::Player`] shape.

use crate::ChessMove;

use super::{PlayerResponse, mailbox::MoveMailbox};

/// Core state for a move source fed from outside the engine.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(in crate::player) struct External {
    mailbox: MoveMailbox,
}

impl External {
    /// Creates an empty external move source with no pending move.
    ///
    /// Backs the non-blocking [`Player`](super::Player) facade: polling
    /// returns pending immediately when no move was submitted.
    pub(in crate::player) const fn new() -> Self {
        Self {
            mailbox: MoveMailbox::new(),
        }
    }

    /// Stages `chess_move` under the single-pending mailbox discipline.
    ///
    /// The move waits until the owning side is polled; [`poll`](Self::poll)
    /// takes it without blocking. Use [`pending`](Self::pending) to peek and
    /// [`cancel`](Self::cancel) to withdraw it before it is consumed.
    ///
    /// # Errors
    ///
    /// Returns [`SubmitError::MovePending`](crate::SubmitError::MovePending)
    /// when a previously submitted move has not been polled or cancelled.
    pub(in crate::player) fn submit(
        &mut self,
        chess_move: ChessMove,
    ) -> Result<(), super::mailbox::SubmitError> {
        self.mailbox.submit(chess_move)
    }

    /// Returns the staged move without consuming it, if any.
    ///
    /// Peeking never affects the single-pending discipline: the move stays
    /// staged until [`poll`](Self::poll) consumes it or
    /// [`cancel`](Self::cancel) withdraws it.
    pub(in crate::player) const fn pending(&self) -> Option<ChessMove> {
        self.mailbox.pending()
    }

    /// Withdraws and returns the staged move, if any.
    ///
    /// Frees the mailbox slot so a replacement move can be submitted before
    /// the next non-blocking [`poll`](Self::poll).
    pub(in crate::player) fn cancel(&mut self) -> Option<ChessMove> {
        self.mailbox.cancel()
    }

    /// Takes the staged move without blocking, or reports pending.
    ///
    /// Never waits for input: returns [`PlayerResponse::Move`] when a move
    /// was submitted and [`PlayerResponse::Pending`] otherwise. Consumed
    /// moves are committed through the session, which validates them
    /// against the authoritative game.
    pub(in crate::player) fn poll(&mut self) -> PlayerResponse {
        self.mailbox.poll()
    }
}
