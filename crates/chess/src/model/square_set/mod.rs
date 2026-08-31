//! Allocation-free sets of board squares.

mod iter;
mod ops;

pub use iter::Squares;

use core::fmt;

use super::Square;

/// A number of squares in the inclusive range from zero through 64.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct SquareCount(u8);

impl SquareCount {
    /// Returns the numeric count at a collection or serialization boundary.
    #[must_use]
    pub const fn value(self) -> u8 {
        self.0
    }
}

impl fmt::Display for SquareCount {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

/// A set of chessboard squares.
///
/// The storage strategy is private. Callers interact only through set
/// semantics and square iteration.
#[derive(Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SquareSet(pub(super) u64);

impl SquareSet {
    /// A set containing no squares.
    pub const EMPTY: Self = Self(0);

    /// A set containing every square.
    pub const FULL: Self = Self(u64::MAX);

    /// Creates a set containing one square.
    #[must_use]
    pub const fn from_square(square: Square) -> Self {
        Self(1_u64 << square.index().value())
    }

    /// Returns the number of contained squares.
    #[must_use]
    pub const fn len(self) -> SquareCount {
        SquareCount(self.0.count_ones() as u8)
    }

    /// Returns `true` when no squares are contained.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// Returns `true` when every square is contained.
    #[must_use]
    pub const fn is_full(self) -> bool {
        self.0 == u64::MAX
    }

    /// Returns whether `square` belongs to this set.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        self.0 & Self::from_square(square).0 != 0
    }

    /// Returns whether this set and `other` share no squares.
    #[must_use]
    pub const fn is_disjoint(self, other: Self) -> bool {
        self.0 & other.0 == 0
    }

    /// Returns whether this set and `other` share at least one square.
    #[must_use]
    pub const fn intersects(self, other: Self) -> bool {
        !self.is_disjoint(other)
    }

    /// Inserts `square`, returning whether it was absent.
    pub fn insert(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_absent = self.0 & mask == 0;
        self.0 |= mask;
        was_absent
    }

    /// Removes `square`, returning whether it was present.
    pub fn remove(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_present = self.0 & mask != 0;
        self.0 &= !mask;
        was_present
    }

    /// Toggles `square` and returns whether it is now present.
    pub fn toggle(&mut self, square: Square) -> bool {
        self.0 ^= Self::from_square(square).0;
        self.contains(square)
    }

    /// Removes every square.
    pub fn clear(&mut self) {
        self.0 = 0;
    }

    /// Returns the lowest-index contained square.
    #[must_use]
    pub const fn first(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_raw_index(self.0.trailing_zeros() as u8)
        }
    }

    /// Returns the highest-index contained square.
    #[must_use]
    pub const fn last(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_raw_index((63 - self.0.leading_zeros()) as u8)
        }
    }

    /// Returns contained squares in board-index order.
    pub const fn iter(self) -> Squares {
        Squares::new(self.0)
    }
}

impl fmt::Debug for SquareSet {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_set().entries(*self).finish()
    }
}
