//! Typed board files and ranks.

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
