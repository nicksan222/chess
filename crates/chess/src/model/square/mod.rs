//! Validated squares and board geometry operations.

mod constants;
mod coordinate;
mod geometry;
mod index;
mod iter;
mod offset;
mod parse;

pub use coordinate::{File, Rank};
pub use geometry::{BoardDirection, BoardEdge};
pub use index::{InvalidSquare, SquareIndex};
pub use iter::{AllSquares, SquareRay};
pub use offset::{FileOffset, RankOffset, SquareOffset};
pub use parse::ParseSquareError;

use core::fmt;

/// A validated square on an 8×8 chessboard.
///
/// Board indices start at `a1`, advance through each file toward `h`, then
/// continue rank by rank until `h8`.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct Square(SquareIndex);

impl Square {
    /// The number of squares on a chessboard.
    pub const COUNT: usize = 64;

    /// Creates a square from validated file and rank values.
    ///
    /// [`File`] and [`Rank`] are already range-checked, so construction
    /// cannot fail. Index layout is `rank * 8 + file` with `a1` at zero.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{File, Rank, Square};
    ///
    /// let square = Square::new(File::E, Rank::Four);
    /// assert_eq!(square, Square::E4);
    /// ```
    #[must_use]
    pub const fn new(file: File, rank: Rank) -> Self {
        Self(SquareIndex(rank.index() * 8 + file.index()))
    }

    /// Creates a square from a validated index.
    ///
    /// Accepts a [`SquareIndex`] in `0..64`, where `0` is `a1` and `63`
    /// is `h8`. For fallible primitive input use `Square::try_from(u8)`.
    #[must_use]
    pub const fn from_index(index: SquareIndex) -> Self {
        Self(index)
    }

    /// Creates a square from a raw index, returning `None` when out of range.
    ///
    /// Accepts `0..64` and returns `None` for larger values. This is the
    /// checked input-boundary form of [`Square::from_raw_index_unchecked`].
    pub(crate) const fn from_raw_index(index: u8) -> Option<Self> {
        match SquareIndex::new(index) {
            Ok(index) => Some(Self(index)),
            Err(_) => None,
        }
    }

    /// Creates a square from a raw index without bounds checking.
    ///
    /// # Panics
    ///
    /// Callers must guarantee `index < 64`; an out-of-range index would
    /// construct an invalid [`Square`]. Internal iterators maintain this
    /// by construction.
    pub(crate) const fn from_raw_index_unchecked(index: u8) -> Self {
        Self(SquareIndex(index))
    }

    /// Returns the square's validated board index.
    ///
    /// The index runs `0..64` from `a1` (zero) through `h8` (63); see
    /// [`SquareIndex`].
    #[must_use]
    pub const fn index(self) -> SquareIndex {
        self.0
    }

    /// Returns the square's file.
    ///
    /// The file is the `a`–`h` coordinate derived as `index % 8`; see
    /// [`File`].
    #[must_use]
    pub const fn file(self) -> File {
        File::ALL[(self.0.value() % 8) as usize]
    }

    /// Returns the square's rank.
    ///
    /// The rank is the `1`–`8` coordinate derived as `index / 8`; see
    /// [`Rank`].
    #[must_use]
    pub const fn rank(self) -> Rank {
        Rank::ALL[(self.0.value() / 8) as usize]
    }

    /// Returns the board edges containing this square.
    ///
    /// Yields zero to two [`BoardEdge`] values: corners yield two,
    /// non-corner edge squares yield one, and interior squares yield
    /// none. See [`Square::is_edge`] and [`Square::is_corner`].
    pub fn edges(self) -> impl Iterator<Item = BoardEdge> {
        BoardEdge::ALL
            .into_iter()
            .filter(move |edge| edge.contains(self))
    }

    /// Returns whether this square lies on any board edge.
    ///
    /// Reports `true` for files `a`/`h` or ranks `1`/`8`; interior
    /// squares return `false`.
    #[must_use]
    pub const fn is_edge(self) -> bool {
        matches!(
            (self.file(), self.rank()),
            (File::A | File::H, _) | (_, Rank::One | Rank::Eight)
        )
    }

    /// Returns whether this square lies at the intersection of two edges.
    ///
    /// Only `a1`, `h1`, `a8`, and `h8` return `true`.
    #[must_use]
    pub const fn is_corner(self) -> bool {
        matches!(
            (self.file(), self.rank()),
            (File::A | File::H, Rank::One | Rank::Eight)
        )
    }

    /// Returns the square at `offset`, if it remains on-board.
    ///
    /// Adds the signed [`SquareOffset`] displacement to the file and
    /// rank. Returns `None` when the result would leave the 8×8 board
    /// instead of wrapping around the edges.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{FileOffset, RankOffset, Square, SquareOffset};
    ///
    /// let offset = SquareOffset::new(FileOffset::TOWARD_H, RankOffset::ZERO);
    /// assert_eq!(Square::E4.offset(offset), Some(Square::F4));
    /// assert_eq!(Square::H4.offset(offset), None);
    /// ```
    #[must_use]
    pub const fn offset(self, offset: SquareOffset) -> Option<Self> {
        let file = self.file().index() as i16 + offset.files().value() as i16;
        let rank = self.rank().index() as i16 + offset.ranks().value() as i16;
        if file >= 0 && file < 8 && rank >= 0 && rank < 8 {
            Some(Self(SquareIndex((rank * 8 + file) as u8)))
        } else {
            None
        }
    }

    /// Returns the adjacent square in `direction`, if it is on-board.
    ///
    /// Steps one square along `direction` (see [`BoardDirection`]) and
    /// returns `None` at the board edge instead of wrapping.
    #[must_use]
    pub const fn step(self, direction: BoardDirection) -> Option<Self> {
        self.offset(direction.offset())
    }

    /// Returns the squares extending from this square in `direction`.
    ///
    /// The starting square is excluded and iteration stops at the board edge.
    ///
    /// The ray always starts from the neighbor in `direction`, so edge
    /// squares facing outward yield an empty [`SquareRay`].
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{BoardDirection, Square};
    ///
    /// let ray: Vec<Square> = Square::A1.ray(BoardDirection::TowardRank8).collect();
    /// assert_eq!(ray.first(), Some(&Square::A2));
    /// ```
    pub fn ray(self, direction: BoardDirection) -> SquareRay {
        SquareRay::new(self.step(direction), direction)
    }

    /// Returns every square from `a1` through `h8`.
    ///
    /// Yields all 64 [`Square`] values in ascending index order via an
    /// [`AllSquares`] iterator.
    pub fn all() -> AllSquares {
        AllSquares::new()
    }
}

impl fmt::Display for Square {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}{}", self.file(), self.rank())
    }
}

impl fmt::Debug for Square {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, formatter)
    }
}

impl From<Square> for SquareIndex {
    fn from(square: Square) -> Self {
        square.index()
    }
}

impl From<SquareIndex> for Square {
    fn from(index: SquareIndex) -> Self {
        Self::from_index(index)
    }
}

impl TryFrom<u8> for Square {
    type Error = InvalidSquare;

    fn try_from(index: u8) -> Result<Self, Self::Error> {
        SquareIndex::new(index).map(Self)
    }
}
