//! Validated zero-based square indices.

use core::fmt;

/// A validated zero-based square index in `0..64`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct SquareIndex(pub(super) u8);

impl SquareIndex {
    /// Creates a validated square index.
    ///
    /// Accepts `0..64` (`a1` through `h8`) and preserves the value for
    /// [`crate::Square`] construction, bit access, and serialization.
    ///
    /// # Errors
    ///
    /// Returns [`InvalidSquare`] when `value` is 64 or greater.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::SquareIndex;
    ///
    /// assert_eq!(SquareIndex::new(0)?.value(), 0);
    /// assert!(SquareIndex::new(64).is_err());
    /// # Ok::<(), chess::InvalidSquare>(())
    /// ```
    pub const fn new(value: u8) -> Result<Self, InvalidSquare> {
        if value < 64 {
            Ok(Self(value))
        } else {
            Err(InvalidSquare { index: value })
        }
    }

    /// Returns the primitive representation for serialization or bit access.
    ///
    /// The result is always in `0..64` and doubles as the bit position in
    /// a [`SquareSet`](crate::SquareSet).
    #[must_use]
    pub const fn value(self) -> u8 {
        self.0
    }
}

impl TryFrom<u8> for SquareIndex {
    type Error = InvalidSquare;

    fn try_from(value: u8) -> Result<Self, Self::Error> {
        Self::new(value)
    }
}

impl From<SquareIndex> for u8 {
    fn from(index: SquareIndex) -> Self {
        index.value()
    }
}

/// The error returned when an index does not identify a chessboard square.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidSquare {
    index: u8,
}

impl InvalidSquare {
    /// Returns the rejected primitive index from the input boundary.
    ///
    /// The value is always 64 or greater: it echoes the input that
    /// [`SquareIndex::new`] (or `Square`/`SquareIndex` `TryFrom<u8>`)
    /// refused.
    #[must_use]
    pub const fn index(self) -> u8 {
        self.index
    }
}

impl fmt::Display for InvalidSquare {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "square index {} is outside 0..64", self.index)
    }
}

impl_error!(InvalidSquare);
