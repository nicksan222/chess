use core::fmt;

/// One of the four objective chessboard edges.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum BoardEdge {
    /// The `a`-file edge.
    FileA,
    /// The `h`-file edge.
    FileH,
    /// The rank-1 edge.
    Rank1,
    /// The rank-8 edge.
    Rank8,
}

impl BoardEdge {
    /// Every edge in file-then-rank order.
    pub const ALL: [Self; 4] = [Self::FileA, Self::FileH, Self::Rank1, Self::Rank8];

    /// Returns whether this edge contains `square`.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        match self {
            Self::FileA => square.file() == 0,
            Self::FileH => square.file() == 7,
            Self::Rank1 => square.rank() == 0,
            Self::Rank8 => square.rank() == 7,
        }
    }
}

/// One of the eight straight or diagonal coordinate directions.
///
/// Names refer to fixed files and ranks, never to a player's perspective.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum BoardDirection {
    /// Toward rank 8.
    TowardRank8,
    /// Toward rank 1.
    TowardRank1,
    /// Toward file `h`.
    TowardFileH,
    /// Toward file `a`.
    TowardFileA,
    /// Toward rank 8 and file `h`.
    TowardRank8FileH,
    /// Toward rank 8 and file `a`.
    TowardRank8FileA,
    /// Toward rank 1 and file `h`.
    TowardRank1FileH,
    /// Toward rank 1 and file `a`.
    TowardRank1FileA,
}

impl BoardDirection {
    const fn delta(self) -> (i8, i8) {
        match self {
            Self::TowardRank8 => (0, 1),
            Self::TowardRank1 => (0, -1),
            Self::TowardFileH => (1, 0),
            Self::TowardFileA => (-1, 0),
            Self::TowardRank8FileH => (1, 1),
            Self::TowardRank8FileA => (-1, 1),
            Self::TowardRank1FileH => (1, -1),
            Self::TowardRank1FileA => (-1, -1),
        }
    }
}

/// A validated square on an 8×8 chessboard.
///
/// Indices use the conventional bitboard mapping: `a1` is 0, files increase
/// toward `h`, ranks increase toward rank 8, and `h8` is 63.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct Square(u8);

impl Square {
    /// The number of squares on a chessboard.
    pub const COUNT: usize = 64;

    /// Creates a square from zero-based file and rank coordinates.
    #[must_use]
    pub const fn new(file: u8, rank: u8) -> Option<Self> {
        if file < 8 && rank < 8 {
            Some(Self(rank * 8 + file))
        } else {
            None
        }
    }

    /// Creates a square from an index in `0..64`.
    #[must_use]
    pub const fn from_index(index: u8) -> Option<Self> {
        if index < 64 { Some(Self(index)) } else { None }
    }

    /// Returns the square's zero-based bitboard index.
    #[must_use]
    pub const fn index(self) -> u8 {
        self.0
    }

    /// Returns the zero-based file, where file `a` is 0.
    #[must_use]
    pub const fn file(self) -> u8 {
        self.0 % 8
    }

    /// Returns the zero-based rank, where rank 1 is 0.
    #[must_use]
    pub const fn rank(self) -> u8 {
        self.0 / 8
    }

    /// Returns the lowercase algebraic file character.
    #[must_use]
    pub const fn file_char(self) -> char {
        (b'a' + self.file()) as char
    }

    /// Returns the one-based algebraic rank number.
    #[must_use]
    pub const fn rank_number(self) -> u8 {
        self.rank() + 1
    }

    /// Returns the square at the signed coordinate offset, if it is on-board.
    #[must_use]
    pub const fn offset(self, file_delta: i8, rank_delta: i8) -> Option<Self> {
        let file = self.file() as i16 + file_delta as i16;
        let rank = self.rank() as i16 + rank_delta as i16;
        if file >= 0 && file < 8 && rank >= 0 && rank < 8 {
            Some(Self((rank * 8 + file) as u8))
        } else {
            None
        }
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
        self.file() == 0 || self.file() == 7 || self.rank() == 0 || self.rank() == 7
    }

    /// Returns whether this square lies at the intersection of two edges.
    #[must_use]
    pub const fn is_corner(self) -> bool {
        (self.file() == 0 || self.file() == 7) && (self.rank() == 0 || self.rank() == 7)
    }

    /// Returns the adjacent square in `direction`, if it is on-board.
    #[must_use]
    pub const fn step(self, direction: BoardDirection) -> Option<Self> {
        let (file_delta, rank_delta) = direction.delta();
        self.offset(file_delta, rank_delta)
    }

    /// Returns the squares extending from this square in `direction`.
    ///
    /// The starting square is excluded and iteration stops at the board edge.
    pub fn ray(self, direction: BoardDirection) -> SquareRay {
        SquareRay {
            next: self.step(direction),
            direction,
        }
    }

    /// Returns every square from `a1` through `h8`.
    pub fn all() -> AllSquares {
        AllSquares { front: 0, back: 64 }
    }
}

macro_rules! define_squares {
    ($($name:ident = $index:literal),+ $(,)?) => {
        impl Square {
            $(
                #[doc = concat!("The `", stringify!($name), "` square.")]
                pub const $name: Self = Self($index);
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
        write!(formatter, "{}{}", self.file_char(), self.rank_number())
    }
}

impl fmt::Debug for Square {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, formatter)
    }
}

impl From<Square> for u8 {
    fn from(square: Square) -> Self {
        square.index()
    }
}

impl From<Square> for usize {
    fn from(square: Square) -> Self {
        usize::from(square.index())
    }
}

impl TryFrom<u8> for Square {
    type Error = InvalidSquare;

    fn try_from(index: u8) -> Result<Self, Self::Error> {
        Self::from_index(index).ok_or(InvalidSquare { index })
    }
}

/// The error returned when an index does not identify a chessboard square.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidSquare {
    index: u8,
}

impl InvalidSquare {
    /// Returns the rejected index.
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

/// An iterator over the squares in one directional ray.
#[derive(Clone, Debug)]
pub struct SquareRay {
    next: Option<Square>,
    direction: BoardDirection,
}

impl Iterator for SquareRay {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        let current = self.next?;
        self.next = current.step(self.direction);
        Some(current)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (0, Some(7))
    }
}

impl core::iter::FusedIterator for SquareRay {}

/// An iterator over all 64 validated chessboard squares.
#[derive(Clone, Debug)]
pub struct AllSquares {
    front: u8,
    back: u8,
}

impl Iterator for AllSquares {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        if self.front == self.back {
            return None;
        }
        let square = Square(self.front);
        self.front += 1;
        Some(square)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = usize::from(self.back - self.front);
        (remaining, Some(remaining))
    }
}

impl DoubleEndedIterator for AllSquares {
    fn next_back(&mut self) -> Option<Self::Item> {
        if self.front == self.back {
            return None;
        }
        self.back -= 1;
        Some(Square(self.back))
    }
}

impl ExactSizeIterator for AllSquares {}
impl core::iter::FusedIterator for AllSquares {}
