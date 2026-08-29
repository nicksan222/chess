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

macro_rules! define_squares {
    ($($name:ident = $index:literal),+ $(,)?) => {
        impl Square {
            $(
                #[doc = concat!("The `", stringify!($name), "` square.")]
                pub const $name: Self = Self(SquareIndex($index));
            )+
        }
    };
}

define_squares! {
    A1 = 0, B1 = 1, C1 = 2, D1 = 3, E1 = 4, F1 = 5, G1 = 6, H1 = 7,
    A2 = 8, B2 = 9, C2 = 10, D2 = 11, E2 = 12, F2 = 13, G2 = 14, H2 = 15,
    A3 = 16, B3 = 17, C3 = 18, D3 = 19, E3 = 20, F3 = 21, G3 = 22, H3 = 23,
    A4 = 24, B4 = 25, C4 = 26, D4 = 27, E4 = 28, F4 = 29, G4 = 30, H4 = 31,
    A5 = 32, B5 = 33, C5 = 34, D5 = 35, E5 = 36, F5 = 37, G5 = 38, H5 = 39,
    A6 = 40, B6 = 41, C6 = 42, D6 = 43, E6 = 44, F6 = 45, G6 = 46, H6 = 47,
    A7 = 48, B7 = 49, C7 = 50, D7 = 51, E7 = 52, F7 = 53, G7 = 54, H7 = 55,
    A8 = 56, B8 = 57, C8 = 58, D8 = 59, E8 = 60, F8 = 61, G8 = 62, H8 = 63,
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
