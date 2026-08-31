//! Iteration over all squares and directional rays.

use super::{BoardDirection, Square};

/// An iterator over the squares in one directional ray.
#[derive(Clone, Debug)]
pub struct SquareRay {
    next: Option<Square>,
    direction: BoardDirection,
}

impl SquareRay {
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
