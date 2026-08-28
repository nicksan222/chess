use core::fmt;

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
