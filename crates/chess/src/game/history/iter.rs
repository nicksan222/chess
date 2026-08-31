use core::iter::FusedIterator;

use chess_core::collections::Iter as LinkedListIter;

use super::HistoryStep;

/// An iterator over hash-linked game-history steps in chronological order.
pub struct GameHistoryIter<'a>(LinkedListIter<'a, HistoryStep>);

impl<'a> GameHistoryIter<'a> {
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
