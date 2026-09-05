//! Chess side values and color operations.

use core::fmt;

/// A chess player's color.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Color {
    /// The player moving first.
    White,
    /// The player moving second.
    Black,
}

impl Color {
    /// Both colors in white-then-black order.
    pub const ALL: [Self; 2] = [Self::White, Self::Black];

    /// Returns the opposing color.
    ///
    /// Maps White to Black and Black to White. The operation is its own
    /// inverse: `color.opposite().opposite() == color`.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::Color;
    ///
    /// assert_eq!(Color::White.opposite(), Color::Black);
    /// ```
    #[must_use]
    pub const fn opposite(self) -> Self {
        match self {
            Self::White => Self::Black,
            Self::Black => Self::White,
        }
    }
}

impl fmt::Display for Color {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::White => "white",
            Self::Black => "black",
        })
    }
}
