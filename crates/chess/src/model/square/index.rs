use core::fmt;

/// A validated zero-based square index in `0..64`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct SquareIndex(pub(super) u8);

impl SquareIndex {
    /// Creates a validated square index.
    pub const fn new(value: u8) -> Result<Self, InvalidSquare> {
        if value < 64 {
            Ok(Self(value))
        } else {
            Err(InvalidSquare { index: value })
        }
    }

    /// Returns the primitive representation for serialization or bit access.
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
