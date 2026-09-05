//! Ordered iteration over squares in a bit set.

use core::iter::FusedIterator;

use crate::Square;

/// An iterator over a [`SquareSet`](crate::SquareSet).
#[derive(Clone, Debug)]
pub struct Squares {
    bits: u64,
}

impl Squares {
    /// Creates an iterator over the squares encoded in `bits`.
    ///
    /// Each set bit at position `i` yields the square with index `i`.
    /// Backs [`SquareSet::iter`](crate::SquareSet) and the
    /// `IntoIterator` impls; iteration order is ascending index order
    /// for [`Iterator::next`] and descending for `next_back`.
    pub(super) const fn new(bits: u64) -> Self {
        Self { bits }
    }
}

impl Iterator for Squares {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        if self.bits == 0 {
            return None;
        }
        let index = self.bits.trailing_zeros() as u8;
        self.bits &= self.bits - 1;
        Square::from_raw_index(index)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.bits.count_ones() as usize;
        (remaining, Some(remaining))
    }
}

impl DoubleEndedIterator for Squares {
    fn next_back(&mut self) -> Option<Self::Item> {
        if self.bits == 0 {
            return None;
        }
        let index = (63 - self.bits.leading_zeros()) as u8;
        self.bits &= !(1_u64 << index);
        Square::from_raw_index(index)
    }
}

impl ExactSizeIterator for Squares {}
impl FusedIterator for Squares {}
