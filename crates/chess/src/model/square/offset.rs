//! Typed file, rank, and square displacements.

use crate::Color;

/// A signed number of files toward `h` (positive) or `a` (negative).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[repr(transparent)]
pub struct FileOffset(i8);

impl FileOffset {
    /// No file displacement.
    pub const ZERO: Self = Self(0);
    /// One file toward `h`.
    pub const TOWARD_H: Self = Self(1);
    /// One file toward `a`.
    pub const TOWARD_A: Self = Self(-1);

    /// Doubles this displacement, as in a knight's longer leg.
    #[must_use]
    pub const fn doubled(self) -> Self {
        Self(self.0 * 2)
    }

    /// Reverses this displacement.
    #[must_use]
    pub const fn reversed(self) -> Self {
        Self(-self.0)
    }

    pub(crate) const fn value(self) -> i8 {
        self.0
    }
}

/// A signed number of ranks toward rank 8 (positive) or rank 1 (negative).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[repr(transparent)]
pub struct RankOffset(i8);

impl RankOffset {
    /// No rank displacement.
    pub const ZERO: Self = Self(0);
    /// One rank toward rank 8.
    pub const TOWARD_RANK_8: Self = Self(1);
    /// One rank toward rank 1.
    pub const TOWARD_RANK_1: Self = Self(-1);

    /// Doubles this displacement, as in a knight's longer leg.
    #[must_use]
    pub const fn doubled(self) -> Self {
        Self(self.0 * 2)
    }

    /// Reverses this displacement.
    #[must_use]
    pub const fn reversed(self) -> Self {
        Self(-self.0)
    }

    /// One rank forward for a pawn of `color`.
    #[must_use]
    pub const fn pawn_push(color: Color) -> Self {
        match color {
            Color::White => Self::TOWARD_RANK_8,
            Color::Black => Self::TOWARD_RANK_1,
        }
    }

    pub(crate) const fn value(self) -> i8 {
        self.0
    }
}

/// A signed file-and-rank displacement on a chessboard.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SquareOffset {
    files: FileOffset,
    ranks: RankOffset,
}

impl SquareOffset {
    /// Creates a displacement from file and rank components.
    #[must_use]
    pub const fn new(files: FileOffset, ranks: RankOffset) -> Self {
        Self { files, ranks }
    }

    /// Returns the file component of this displacement.
    #[must_use]
    pub const fn files(self) -> FileOffset {
        self.files
    }

    /// Returns the rank component of this displacement.
    #[must_use]
    pub const fn ranks(self) -> RankOffset {
        self.ranks
    }
}
