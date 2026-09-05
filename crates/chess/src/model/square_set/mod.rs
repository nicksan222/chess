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
    ///
    /// The value ranges from `0` (empty) through `64` (full) and is
    /// produced by [`SquareSet::len`].
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
    ///
    /// Sets the bit at `square.index().value()` and leaves all other
    /// bits clear. This is also available via `SquareSet::from(square)`.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Square, SquareSet};
    ///
    /// let set = SquareSet::from_square(Square::E4);
    /// assert!(set.contains(Square::E4));
    /// ```
    #[must_use]
    pub const fn from_square(square: Square) -> Self {
        Self(1_u64 << square.index().value())
    }

    /// Returns the number of contained squares.
    ///
    /// Counts the set bits, yielding `0` for [`SquareSet::EMPTY`] and
    /// `64` for [`SquareSet::FULL`].
    #[must_use]
    pub const fn len(self) -> SquareCount {
        SquareCount(self.0.count_ones() as u8)
    }

    /// Returns `true` when no squares are contained.
    ///
    /// Equivalent to `set.len().value() == 0`; provided so callers need
    /// not count bits for the common emptiness check.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// Returns `true` when every square is contained.
    ///
    /// Equivalent to `set.len().value() == 64`; only [`SquareSet::FULL`]
    /// (or its bitwise equivalents) satisfies this.
    #[must_use]
    pub const fn is_full(self) -> bool {
        self.0 == u64::MAX
    }

    /// Returns whether `square` belongs to this set.
    ///
    /// Tests the bit at `square.index().value()`. Empty sets contain
    /// nothing and [`SquareSet::FULL`] contains every square.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        self.0 & Self::from_square(square).0 != 0
    }

    /// Returns whether this set and `other` share no squares.
    ///
    /// A set is disjoint from itself only when it is empty. See also
    /// [`SquareSet::intersects`].
    #[must_use]
    pub const fn is_disjoint(self, other: Self) -> bool {
        self.0 & other.0 == 0
    }

    /// Returns whether this set and `other` share at least one square.
    ///
    /// This is the negation of [`SquareSet::is_disjoint`].
    #[must_use]
    pub const fn intersects(self, other: Self) -> bool {
        !self.is_disjoint(other)
    }

    /// Inserts `square`, returning whether it was absent.
    ///
    /// Sets the square's bit. Returns `true` when the square is newly
    /// added and `false` when it was already present.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Square, SquareSet};
    ///
    /// let mut set = SquareSet::EMPTY;
    /// assert!(set.insert(Square::E4));
    /// assert!(!set.insert(Square::E4));
    /// ```
    pub fn insert(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_absent = self.0 & mask == 0;
        self.0 |= mask;
        was_absent
    }

    /// Removes `square`, returning whether it was present.
    ///
    /// Clears the square's bit. Returns `true` when the square was
    /// present and `false` when the set is unchanged.
    pub fn remove(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_present = self.0 & mask != 0;
        self.0 &= !mask;
        was_present
    }

    /// Toggles `square` and returns whether it is now present.
    ///
    /// Flips the square's bit: present squares are removed (`false`)
    /// and absent squares are inserted (`true`).
    pub fn toggle(&mut self, square: Square) -> bool {
        self.0 ^= Self::from_square(square).0;
        self.contains(square)
    }

    /// Removes every square.
    ///
    /// Resets all bits, making the set equal to [`SquareSet::EMPTY`].
    pub fn clear(&mut self) {
        self.0 = 0;
    }

    /// Returns the lowest-index contained square.
    ///
    /// Scans from `a1` upward and returns `None` for an empty set.
    /// Useful for draining a set from the lowest square.
    #[must_use]
    pub const fn first(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_raw_index(self.0.trailing_zeros() as u8)
        }
    }

    /// Returns the highest-index contained square.
    ///
    /// Scans from `h8` downward and returns `None` for an empty set.
    /// Useful for draining a set from the highest square.
    #[must_use]
    pub const fn last(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_raw_index((63 - self.0.leading_zeros()) as u8)
        }
    }

    /// Returns contained squares in board-index order.
    ///
    /// Yields each member from `a1` through `h8` via a [`Squares`]
    /// iterator. The same order is available through `IntoIterator` for
    /// [`SquareSet`] and `&SquareSet`.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Square, SquareSet};
    ///
    /// let set = SquareSet::from_square(Square::A1) | SquareSet::from_square(Square::H8);
    /// let squares: Vec<Square> = set.iter().collect();
    /// assert_eq!(squares, vec![Square::A1, Square::H8]);
    /// ```
    pub const fn iter(self) -> Squares {
        Squares::new(self.0)
    }
}

impl fmt::Debug for SquareSet {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_set().entries(*self).finish()
    }
}
