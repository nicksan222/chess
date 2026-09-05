//! Stable player facade and restricted interaction boundary.

mod computer;
mod error;
mod external;
mod human;
mod mailbox;
mod online;
mod view;

use crate::ChessMove;

pub use computer::{ComputerError, Difficulty};
pub use error::PlayerError;
pub use mailbox::SubmitError;
pub(crate) use view::PlayerView;

use self::{computer::Computer, human::Human, online::Online};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PlayerResponse {
    Pending,
    Move(ChessMove),
}

/// A chess participant independent of how its moves are produced.
///
/// Human, computer, and online players share this one stable type, allowing an
/// application to select a play mode at runtime without naming implementation
/// details.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Player {
    pub(in crate::player) kind: PlayerKind,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(in crate::player) enum PlayerKind {
    Human(Human),
    Computer(Computer),
    Online(Online),
}

impl Player {
    /// Builds a [`Player`] from its internal move-source kind.
    ///
    /// Used by the [`Player::human`], [`Player::computer`], and
    /// [`Player::online`] constructors so every kind shares the one stable
    /// facade polled non-blockingly by [`crate::GameSession`].
    pub(in crate::player) const fn from_kind(kind: PlayerKind) -> Self {
        Self { kind }
    }

    /// Submits a move observed locally or received online.
    ///
    /// Stages `chess_move` under the mailbox single-pending discipline: at
    /// most one move waits for the owning side's next non-blocking poll.
    /// Nothing blocks here; the staged move is validated against the
    /// authoritative game only when [`crate::GameSession::poll`] consumes it.
    /// Peek with [`pending_move`](Self::pending_move) and withdraw with
    /// [`cancel`](Self::cancel).
    ///
    /// # Errors
    ///
    /// Returns [`SubmitError::ComputerControlled`] for computer players,
    /// which search synchronously instead of consuming submissions, and
    /// [`SubmitError::MovePending`] when a staged move has not been polled
    /// or cancelled yet.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Player, Square};
    ///
    /// let mut player = Player::human();
    /// let chess_move = ChessMove::new(Square::E2, Square::E4);
    /// player.submit(chess_move)?;
    /// assert_eq!(player.pending_move(), Some(chess_move));
    /// # Ok::<(), chess::SubmitError>(())
    /// ```
    pub fn submit(&mut self, chess_move: ChessMove) -> Result<(), SubmitError> {
        match &mut self.kind {
            PlayerKind::Human(human) => human.inner.submit(chess_move),
            PlayerKind::Online(online) => online.inner.submit(chess_move),
            PlayerKind::Computer(_) => Err(SubmitError::ComputerControlled),
        }
    }

    /// Returns the submitted move waiting for this player's turn, if any.
    ///
    /// Peeks at the single-pending mailbox slot without consuming it: the
    /// move stays staged until a non-blocking [`crate::GameSession::poll`]
    /// consumes it or [`cancel`](Self::cancel) withdraws it. Computer
    /// players search synchronously and always report `None`.
    #[must_use]
    pub const fn pending_move(&self) -> Option<ChessMove> {
        match &self.kind {
            PlayerKind::Human(human) => human.inner.pending(),
            PlayerKind::Online(online) => online.inner.pending(),
            PlayerKind::Computer(_) => None,
        }
    }

    /// Cancels and returns the pending submitted move, if any.
    ///
    /// Withdraws the staged move under the mailbox single-pending
    /// discipline, freeing the slot for a replacement before the next
    /// non-blocking [`crate::GameSession::poll`]. Computer players hold no
    /// staged move and always report `None`.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Player, Square};
    ///
    /// let mut player = Player::human();
    /// let chess_move = ChessMove::new(Square::E2, Square::E4);
    /// player.submit(chess_move).expect("empty mailbox accepts");
    /// assert_eq!(player.cancel(), Some(chess_move));
    /// assert_eq!(player.pending_move(), None);
    /// ```
    pub fn cancel(&mut self) -> Option<ChessMove> {
        match &mut self.kind {
            PlayerKind::Human(human) => human.inner.cancel(),
            PlayerKind::Online(online) => online.inner.cancel(),
            PlayerKind::Computer(_) => None,
        }
    }

    /// Polls this player against a restricted position view.
    ///
    /// Human and online sources return their staged move without blocking,
    /// or pending when the mailbox is empty. Computer sources search
    /// synchronously using only the [`PlayerView`] capabilities and never
    /// mutate game state. [`crate::GameSession`] polls only the side to move
    /// and validates consumed moves authoritatively.
    ///
    /// # Errors
    ///
    /// Returns [`PlayerError::Computer`] when the synchronous search or its
    /// position translation fails, including engine/divergence reports such
    /// as [`ComputerError::IllegalMove`] and [`ComputerError::Resigned`].
    pub(crate) fn poll(&mut self, view: PlayerView<'_>) -> Result<PlayerResponse, PlayerError> {
        match &mut self.kind {
            PlayerKind::Human(human) => Ok(human.poll()),
            PlayerKind::Computer(computer) => computer.poll(view).map_err(PlayerError::Computer),
            PlayerKind::Online(online) => Ok(online.poll()),
        }
    }
}
