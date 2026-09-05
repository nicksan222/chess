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
    ///
    /// Multiplies the signed file count by two, preserving direction.
    /// Combined with a single orthogonal step this forms the knight's
    /// L-shape; doubling [`FileOffset::ZERO`] stays zero.
    #[must_use]
    pub const fn doubled(self) -> Self {
        Self(self.0 * 2)
    }

    /// Reverses this displacement.
    ///
    /// Negates the signed file count, mirroring the step toward the
    /// opposite file edge. Reversing twice returns the original value.
    #[must_use]
    pub const fn reversed(self) -> Self {
        Self(-self.0)
    }

    /// Returns the signed file count (negative toward `a`).
    ///
    /// Used by [`Square::offset`](crate::Square) arithmetic; `0` means
    /// no file movement.
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
    ///
    /// Multiplies the signed rank count by two, preserving direction.
    /// Combined with a single orthogonal step this forms the knight's
    /// L-shape; doubling [`RankOffset::ZERO`] stays zero.
    #[must_use]
    pub const fn doubled(self) -> Self {
        Self(self.0 * 2)
    }

    /// Reverses this displacement.
    ///
    /// Negates the signed rank count, mirroring the step toward the
    /// opposite rank edge. Reversing twice returns the original value.
    #[must_use]
    pub const fn reversed(self) -> Self {
        Self(-self.0)
    }

    /// One rank forward for a pawn of `color`.
    ///
    /// Returns [`RankOffset::TOWARD_RANK_8`] for White and
    /// [`RankOffset::TOWARD_RANK_1`] for Black. Forward always means
    /// toward the opponent's back rank, never toward the pawn's own.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Color, RankOffset};
    ///
    /// assert_eq!(RankOffset::pawn_push(Color::White), RankOffset::TOWARD_RANK_8);
    /// ```
    #[must_use]
    pub const fn pawn_push(color: Color) -> Self {
        match color {
            Color::White => Self::TOWARD_RANK_8,
            Color::Black => Self::TOWARD_RANK_1,
        }
    }

    /// Returns the signed rank count (negative toward rank 1).
    ///
    /// Used by [`Square::offset`](crate::Square) arithmetic; `0` means
    /// no rank movement.
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
    ///
    /// Either component may be zero for a straight displacement; both
    /// nonzero selects a diagonal and equal magnitudes at knight ratios
    /// build knight steps. Applied with [`Square::offset`](crate::Square)
    /// and rejected with `None` when the result leaves the board.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{FileOffset, RankOffset, Square, SquareOffset};
    ///
    /// let knight = SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_8.doubled());
    /// assert_eq!(Square::B1.offset(knight), Some(Square::C3));
    /// ```
    #[must_use]
    pub const fn new(files: FileOffset, ranks: RankOffset) -> Self {
        Self { files, ranks }
    }

    /// Returns the file component of this displacement.
    ///
    /// A [`FileOffset::ZERO`] value means the displacement runs purely
    /// along a rank.
    #[must_use]
    pub const fn files(self) -> FileOffset {
        self.files
    }

    /// Returns the rank component of this displacement.
    ///
    /// A [`RankOffset::ZERO`] value means the displacement runs purely
    /// along a file.
    #[must_use]
    pub const fn ranks(self) -> RankOffset {
        self.ranks
    }
}
