//! Transport-fed online move source.

use super::super::{PlayerResponse, external::External};

/// Internal state for an online player.
///
/// Wraps the shared external-move core; distinct from [`super::human::Human`]
/// so transport concerns (authentication, timeouts, peer identity) have a home
/// without affecting locally observed play.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(in crate::player) struct Online {
    pub(in crate::player) inner: External,
}

impl Online {
    /// Creates an online source with an empty external move core.
    ///
    /// The source polls without blocking and stages at most one
    /// transport-fed move until the session consumes it.
    pub(super) const fn new() -> Self {
        Self {
            inner: External::new(),
        }
    }

    /// Takes the transport-fed move without blocking, or pends.
    ///
    /// Delegates to the shared external-move core under its single-pending
    /// discipline: a submitted move is consumed once, and polling with no
    /// staged move reports pending so [`crate::GameSession`]
    /// can return [`crate::SessionUpdate::Pending`].
    pub(in crate::player) fn poll(&mut self) -> PlayerResponse {
        self.inner.poll()
    }
}
