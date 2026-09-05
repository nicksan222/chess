//! Chronological iteration over authoritative history steps.

use core::iter::FusedIterator;

use chess_core::collections::Iter as LinkedListIter;

use super::HistoryStep;

/// An iterator over hash-linked game-history steps in chronological order.
pub struct GameHistoryIter<'a>(LinkedListIter<'a, HistoryStep>);

impl<'a> GameHistoryIter<'a> {
    /// Creates an iterator over the retained timeline in ply order.
    ///
    /// The iterator borrows the [`GameHistory`](crate::GameHistory) steps
    /// chronologically from [`Ply::FIRST`](crate::Ply) up to the tip. It
    /// performs no hash-chain validation; use
    /// [`GameHistory::verify`](crate::GameHistory::verify) to recheck the
    /// anchor-to-tip links.
    pub(super) const fn new(iter: LinkedListIter<'a, HistoryStep>) -> Self {
        Self(iter)
    }
}

impl<'a> Iterator for GameHistoryIter<'a> {
    type Item = &'a HistoryStep;

    fn next(&mut self) -> Option<Self::Item> {
        self.0.next()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        self.0.size_hint()
    }
}

impl ExactSizeIterator for GameHistoryIter<'_> {}
impl FusedIterator for GameHistoryIter<'_> {}
