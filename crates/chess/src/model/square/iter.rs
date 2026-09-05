//! Iteration over all squares and directional rays.

use super::{BoardDirection, Square};

/// An iterator over the squares in one directional ray.
#[derive(Clone, Debug)]
pub struct SquareRay {
    next: Option<Square>,
    direction: BoardDirection,
}

impl SquareRay {
    /// Creates a ray resuming at `next` and advancing in `direction`.
    ///
    /// `next` is the first square to yield (already the neighbor of the
    /// ray origin, see [`Square::ray`]); `None` produces an empty ray.
    /// Each [`Iterator::next`] call then steps one square further until
    /// the board edge.
    pub(super) const fn new(next: Option<Square>, direction: BoardDirection) -> Self {
        Self { next, direction }
    }
}

impl Iterator for SquareRay {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        let current = self.next?;
        self.next = current.step(self.direction);
        Some(current)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (0, Some(7))
    }
}

impl core::iter::FusedIterator for SquareRay {}

/// An iterator over all 64 validated chessboard squares.
#[derive(Clone, Debug)]
pub struct AllSquares {
    front: u8,
    back: u8,
}

impl AllSquares {
    /// Creates an iterator over squares `a1` through `h8` in index order.
    ///
    /// Backs [`Square::all`]. The range is fixed at all 64 squares, so
    /// the iterator is [`ExactSizeIterator`] with length 64 when fresh.
    pub(super) const fn new() -> Self {
        Self { front: 0, back: 64 }
    }
}

impl Iterator for AllSquares {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        if self.front == self.back {
            return None;
        }
        let square = Square::from_raw_index_unchecked(self.front);
        self.front += 1;
        Some(square)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = usize::from(self.back - self.front);
        (remaining, Some(remaining))
    }
}

impl DoubleEndedIterator for AllSquares {
    fn next_back(&mut self) -> Option<Self::Item> {
        if self.front == self.back {
            return None;
        }
        self.back -= 1;
        Some(Square::from_raw_index_unchecked(self.back))
    }
}

impl ExactSizeIterator for AllSquares {}
impl core::iter::FusedIterator for AllSquares {}
