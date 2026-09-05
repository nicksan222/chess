//! Local human move source.

use super::super::{PlayerResponse, external::External};

/// Internal state for a local human player.
///
/// Wraps the shared external-move core; distinct from [`super::online::Online`]
/// so locally observed moves can evolve independently of transport-fed moves.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(in crate::player) struct Human {
    pub(in crate::player) inner: External,
}

impl Human {
    /// Creates a human source with an empty external move core.
    ///
    /// The source polls without blocking and stages at most one submitted
    /// move until the session consumes it.
    pub(super) const fn new() -> Self {
        Self {
            inner: External::new(),
        }
    }

    /// Takes the locally observed move without blocking, or pends.
    ///
    /// Delegates to the shared external-move core under its single-pending
    /// discipline: a submitted move is consumed once, and polling with no
    /// staged move reports pending so [`crate::GameSession`]
    /// can return [`crate::SessionUpdate::Pending`].
    pub(in crate::player) fn poll(&mut self) -> PlayerResponse {
        self.inner.poll()
    }
}
