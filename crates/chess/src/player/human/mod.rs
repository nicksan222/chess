//! Local human player construction.

mod source;

pub(super) use source::Human;

use crate::Player;
use crate::player::PlayerKind;

impl Player {
    /// Creates a local human player awaiting observed moves.
    ///
    /// Human players never block: [`GameSession::poll`](crate::GameSession::poll)
    /// reports [`SessionUpdate::Pending`](crate::SessionUpdate::Pending) until
    /// a move is staged with [`Player::submit`]. At most one move stays
    /// staged under the mailbox single-pending discipline.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::Player;
    ///
    /// let player = Player::human();
    /// assert_eq!(player.pending_move(), None);
    /// assert_eq!(player.difficulty(), None);
    /// ```
    #[must_use]
    pub const fn human() -> Self {
        Self::from_kind(PlayerKind::Human(Human::new()))
    }
}
