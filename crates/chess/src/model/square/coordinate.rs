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
    ///
    /// Maps `a`–`h` to `'a'`–`'h'`. Used by [`Square`](crate::Square)
    /// formatting and coordinate parsing.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::File;
    ///
    /// assert_eq!(File::E.character(), 'e');
    /// ```
    #[must_use]
    pub const fn character(self) -> char {
        (b'a' + self as u8) as char
    }

    /// Returns the zero-based file number (`a` = 0 through `h` = 7).
    ///
    /// Backs square index arithmetic (`index % 8` and `index / 8`).
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

    /// Returns the zero-based rank number (`1` = 0 through `8` = 7).
    ///
    /// Backs square index arithmetic (`index / 8`). Display and
    /// algebraic output add one to obtain the human `1`–`8` label.
    pub(crate) const fn index(self) -> u8 {
        self as u8
    }
}

impl fmt::Display for Rank {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", *self as u8 + 1)
    }
}
