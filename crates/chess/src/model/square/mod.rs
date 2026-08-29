mod constants;
mod coordinate;
mod geometry;
mod index;
mod iter;

pub use coordinate::{File, Rank};
pub use geometry::{BoardDirection, BoardEdge, SquareOffset};
pub use index::{InvalidSquare, SquareIndex};
pub use iter::{AllSquares, SquareRay};

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
    #[must_use]
    pub const fn new(file: File, rank: Rank) -> Self {
        Self(SquareIndex(rank.index() * 8 + file.index()))
    }

    /// Creates a square from a validated index.
    #[must_use]
    pub const fn from_index(index: SquareIndex) -> Self {
        Self(index)
    }

    pub(crate) const fn from_raw_index(index: u8) -> Option<Self> {
        match SquareIndex::new(index) {
            Ok(index) => Some(Self(index)),
            Err(_) => None,
        }
    }

    pub(crate) const fn from_raw_index_unchecked(index: u8) -> Self {
        Self(SquareIndex(index))
    }

    /// Returns the square's validated board index.
    #[must_use]
    pub const fn index(self) -> SquareIndex {
        self.0
    }

    /// Returns the square's file.
    #[must_use]
    pub const fn file(self) -> File {
        File::ALL[(self.0.value() % 8) as usize]
    }

    /// Returns the square's rank.
    #[must_use]
    pub const fn rank(self) -> Rank {
        Rank::ALL[(self.0.value() / 8) as usize]
    }

    /// Returns the board edges containing this square.
    pub fn edges(self) -> impl Iterator<Item = BoardEdge> {
        BoardEdge::ALL
            .into_iter()
            .filter(move |edge| edge.contains(self))
    }

    /// Returns whether this square lies on any board edge.
    #[must_use]
    pub const fn is_edge(self) -> bool {
        matches!(
            (self.file(), self.rank()),
            (File::A | File::H, _) | (_, Rank::One | Rank::Eight)
        )
    }

    /// Returns whether this square lies at the intersection of two edges.
    #[must_use]
    pub const fn is_corner(self) -> bool {
        matches!(
            (self.file(), self.rank()),
            (File::A | File::H, Rank::One | Rank::Eight)
        )
    }

    /// Returns the square at `offset`, if it remains on-board.
    #[must_use]
    pub const fn offset(self, offset: SquareOffset) -> Option<Self> {
        let file = self.file().index() as i16 + offset.files() as i16;
        let rank = self.rank().index() as i16 + offset.ranks() as i16;
        if file >= 0 && file < 8 && rank >= 0 && rank < 8 {
            Some(Self(SquareIndex((rank * 8 + file) as u8)))
        } else {
            None
        }
    }

    /// Returns the adjacent square in `direction`, if it is on-board.
    #[must_use]
    pub const fn step(self, direction: BoardDirection) -> Option<Self> {
        self.offset(direction.offset())
    }

    /// Returns the squares extending from this square in `direction`.
    ///
    /// The starting square is excluded and iteration stops at the board edge.
    pub fn ray(self, direction: BoardDirection) -> SquareRay {
        SquareRay::new(self.step(direction), direction)
    }

    /// Returns every square from `a1` through `h8`.
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
