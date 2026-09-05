//! Transport-neutral online player construction.

mod source;

pub(super) use source::Online;

use crate::Player;
use crate::player::PlayerKind;

impl Player {
    /// Creates a player whose moves arrive from an external transport.
    ///
    /// Online players share the human non-blocking mailbox semantics: polling
    /// via [`GameSession::poll`](crate::GameSession::poll) reports
    /// [`SessionUpdate::Pending`](crate::SessionUpdate::Pending) until a move
    /// is staged with [`Player::submit`], and at most one move stays staged.
    /// The kind stays distinct from human play so transport, authentication,
    /// or timeout metadata can diverge later.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::Player;
    ///
    /// let player = Player::online();
    /// assert_eq!(player.pending_move(), None);
    /// assert_eq!(player.difficulty(), None);
    /// ```
    #[must_use]
    pub const fn online() -> Self {
        Self::from_kind(PlayerKind::Online(Online::new()))
    }
}
