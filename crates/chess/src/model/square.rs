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
pub struct SquareIndex(u8);

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
        matches!(
            (self, square.file(), square.rank()),
            (Self::FileA, File::A, _)
                | (Self::FileH, File::H, _)
                | (Self::Rank1, _, Rank::One)
                | (Self::Rank8, _, Rank::Eight)
        )
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
    const fn offset(self) -> SquareOffset {
        match self {
            Self::TowardRank8 => SquareOffset::new(0, 1),
            Self::TowardRank1 => SquareOffset::new(0, -1),
            Self::TowardFileH => SquareOffset::new(1, 0),
            Self::TowardFileA => SquareOffset::new(-1, 0),
            Self::TowardRank8FileH => SquareOffset::new(1, 1),
            Self::TowardRank8FileA => SquareOffset::new(-1, 1),
            Self::TowardRank1FileH => SquareOffset::new(1, -1),
            Self::TowardRank1FileA => SquareOffset::new(-1, -1),
        }
    }
}

/// A signed file-and-rank displacement on a chessboard.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SquareOffset {
    files: i8,
    ranks: i8,
}

impl SquareOffset {
    /// Creates a displacement from signed file and rank components.
    #[must_use]
    pub const fn new(files: i8, ranks: i8) -> Self {
        Self { files, ranks }
    }

    pub(crate) const fn files(self) -> i8 {
        self.files
    }

    pub(crate) const fn ranks(self) -> i8 {
        self.ranks
    }
}

/// A validated square on an 8×8 chessboard.
///
/// Indices use the conventional bitboard mapping: `a1` is first, files
/// increase toward `h`, ranks increase toward rank 8, and `h8` is last.
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

    /// Returns the square's validated bitboard index.
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
        let square = Square(SquareIndex(self.front));
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
        Some(Square(SquareIndex(self.back)))
    }
}

impl ExactSizeIterator for AllSquares {}
impl core::iter::FusedIterator for AllSquares {}
