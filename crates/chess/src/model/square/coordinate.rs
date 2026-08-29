use core::fmt;

/// A chessboard file in `a`-through-`h` order.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum File {
    /// File `a`.
    A,
    /// File `b`.
    B,
    /// File `c`.
    C,
    /// File `d`.
    D,
    /// File `e`.
    E,
    /// File `f`.
    F,
    /// File `g`.
    G,
    /// File `h`.
    H,
}

impl File {
    /// All files in `a`-through-`h` order.
    pub const ALL: [Self; 8] = [
        Self::A,
        Self::B,
        Self::C,
        Self::D,
        Self::E,
        Self::F,
        Self::G,
        Self::H,
    ];

    /// Returns the lowercase algebraic file character.
    #[must_use]
    pub const fn character(self) -> char {
        (b'a' + self as u8) as char
    }

    pub(crate) const fn index(self) -> u8 {
        self as u8
    }
}

impl fmt::Display for File {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::A => "a",
            Self::B => "b",
            Self::C => "c",
            Self::D => "d",
            Self::E => "e",
            Self::F => "f",
            Self::G => "g",
            Self::H => "h",
        })
    }
}

/// A chessboard rank in `1`-through-`8` order.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum Rank {
    /// Rank `1`.
    One,
    /// Rank `2`.
    Two,
    /// Rank `3`.
    Three,
    /// Rank `4`.
    Four,
    /// Rank `5`.
    Five,
    /// Rank `6`.
    Six,
    /// Rank `7`.
    Seven,
    /// Rank `8`.
    Eight,
}

impl Rank {
    /// All ranks in `1`-through-`8` order.
    pub const ALL: [Self; 8] = [
        Self::One,
        Self::Two,
        Self::Three,
        Self::Four,
        Self::Five,
        Self::Six,
        Self::Seven,
        Self::Eight,
    ];

    pub(crate) const fn index(self) -> u8 {
        self as u8
    }
}

impl fmt::Display for Rank {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", *self as u8 + 1)
    }
}

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

impl core::error::Error for InvalidSquare {}
