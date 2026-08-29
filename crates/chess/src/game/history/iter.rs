use core::iter::FusedIterator;

use chess_core::collections::Iter as LinkedListIter;

use super::MoveStep;

/// An iterator over hash-linked move steps in chronological order.
pub struct MoveHistoryIter<'a>(LinkedListIter<'a, MoveStep>);

impl<'a> MoveHistoryIter<'a> {
    pub(super) const fn new(iter: LinkedListIter<'a, MoveStep>) -> Self {
        Self(iter)
    }
}

impl<'a> Iterator for MoveHistoryIter<'a> {
    type Item = &'a MoveStep;

    fn next(&mut self) -> Option<Self::Item> {
        self.0.next()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        self.0.size_hint()
    }
}

impl ExactSizeIterator for MoveHistoryIter<'_> {}
impl FusedIterator for MoveHistoryIter<'_> {}
