use core::{
    fmt,
    iter::FusedIterator,
    ops::{
        BitAnd, BitAndAssign, BitOr, BitOrAssign, BitXor, BitXorAssign, Not, Shl, ShlAssign, Shr,
        ShrAssign, Sub, SubAssign,
    },
};

use super::Square;

/// A compact set of chessboard squares stored in one 64-bit word.
#[derive(Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct BitBoard(u64);

impl BitBoard {
    /// A bitboard containing no squares.
    pub const EMPTY: Self = Self(0);

    /// A bitboard containing all squares.
    pub const FULL: Self = Self(u64::MAX);

    /// The `a`-file mask.
    pub const FILE_A: Self = Self(0x0101_0101_0101_0101);

    /// The `h`-file mask.
    pub const FILE_H: Self = Self(0x8080_8080_8080_8080);

    /// Creates a bitboard from its raw representation.
    #[must_use]
    pub const fn from_bits(bits: u64) -> Self {
        Self(bits)
    }

    /// Creates a bitboard containing one square.
    #[must_use]
    pub const fn from_square(square: Square) -> Self {
        Self(1_u64 << square.index())
    }

    /// Returns the raw 64-bit representation.
    #[must_use]
    pub const fn bits(self) -> u64 {
        self.0
    }

    /// Returns the number of contained squares.
    #[must_use]
    pub const fn len(self) -> u32 {
        self.0.count_ones()
    }

    /// Returns `true` when no squares are contained.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// Returns `true` when every square is contained.
    #[must_use]
    pub const fn is_full(self) -> bool {
        self.0 == u64::MAX
    }

    /// Returns `true` when `square` is contained.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        self.0 & Self::from_square(square).0 != 0
    }

    /// Returns `true` when this board and `other` share no squares.
    #[must_use]
    pub const fn is_disjoint(self, other: Self) -> bool {
        self.0 & other.0 == 0
    }

    /// Returns `true` when this board and `other` share at least one square.
    #[must_use]
    pub const fn intersects(self, other: Self) -> bool {
        !self.is_disjoint(other)
    }

    /// Inserts `square`, returning `true` if it was not already present.
    pub fn insert(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_absent = self.0 & mask == 0;
        self.0 |= mask;
        was_absent
    }

    /// Removes `square`, returning `true` if it was present.
    pub fn remove(&mut self, square: Square) -> bool {
        let mask = Self::from_square(square).0;
        let was_present = self.0 & mask != 0;
        self.0 &= !mask;
        was_present
    }

    /// Toggles `square` and returns whether it is now present.
    pub fn toggle(&mut self, square: Square) -> bool {
        self.0 ^= Self::from_square(square).0;
        self.contains(square)
    }

    /// Removes all squares.
    pub fn clear(&mut self) {
        self.0 = 0;
    }

    /// Returns the lowest-index contained square.
    #[must_use]
    pub const fn first(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_index(self.0.trailing_zeros() as u8)
        }
    }

    /// Returns the highest-index contained square.
    #[must_use]
    pub const fn last(self) -> Option<Square> {
        if self.is_empty() {
            None
        } else {
            Square::from_index((63 - self.0.leading_zeros()) as u8)
        }
    }

    /// Returns squares in ascending bit-index order.
    pub const fn iter(self) -> Squares {
        Squares { bits: self.0 }
    }

    /// Shifts all bits toward higher indices, discarding overflow.
    ///
    /// Shifts of 64 or more produce an empty board.
    #[must_use]
    pub const fn shift_left(self, amount: u32) -> Self {
        match self.0.checked_shl(amount) {
            Some(bits) => Self(bits),
            None => Self::EMPTY,
        }
    }

    /// Shifts all bits toward lower indices, discarding underflow.
    ///
    /// Shifts of 64 or more produce an empty board.
    #[must_use]
    pub const fn shift_right(self, amount: u32) -> Self {
        match self.0.checked_shr(amount) {
            Some(bits) => Self(bits),
            None => Self::EMPTY,
        }
    }

    /// Moves squares one rank north, discarding rank 8.
    #[must_use]
    pub const fn north(self) -> Self {
        self.shift_left(8)
    }

    /// Moves squares one rank south, discarding rank 1.
    #[must_use]
    pub const fn south(self) -> Self {
        self.shift_right(8)
    }

    /// Moves squares one file east without wrapping from `h` to `a`.
    #[must_use]
    pub const fn east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) << 1)
    }

    /// Moves squares one file west without wrapping from `a` to `h`.
    #[must_use]
    pub const fn west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) >> 1)
    }

    /// Moves squares one step north-east without file wrapping.
    #[must_use]
    pub const fn north_east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) << 9)
    }

    /// Moves squares one step north-west without file wrapping.
    #[must_use]
    pub const fn north_west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) << 7)
    }

    /// Moves squares one step south-east without file wrapping.
    #[must_use]
    pub const fn south_east(self) -> Self {
        Self((self.0 & !Self::FILE_H.0) >> 7)
    }

    /// Moves squares one step south-west without file wrapping.
    #[must_use]
    pub const fn south_west(self) -> Self {
        Self((self.0 & !Self::FILE_A.0) >> 9)
    }
}

impl fmt::Debug for BitBoard {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_set().entries(*self).finish()
    }
}

impl From<Square> for BitBoard {
    fn from(square: Square) -> Self {
        Self::from_square(square)
    }
}

impl From<u64> for BitBoard {
    fn from(bits: u64) -> Self {
        Self::from_bits(bits)
    }
}

impl From<BitBoard> for u64 {
    fn from(board: BitBoard) -> Self {
        board.bits()
    }
}

impl FromIterator<Square> for BitBoard {
    fn from_iter<I: IntoIterator<Item = Square>>(iter: I) -> Self {
        let mut board = Self::EMPTY;
        board.extend(iter);
        board
    }
}

impl Extend<Square> for BitBoard {
    fn extend<I: IntoIterator<Item = Square>>(&mut self, iter: I) {
        for square in iter {
            self.insert(square);
        }
    }
}

impl<'a> Extend<&'a Square> for BitBoard {
    fn extend<I: IntoIterator<Item = &'a Square>>(&mut self, iter: I) {
        self.extend(iter.into_iter().copied());
    }
}

impl IntoIterator for BitBoard {
    type Item = Square;
    type IntoIter = Squares;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

impl IntoIterator for &BitBoard {
    type Item = Square;
    type IntoIter = Squares;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

macro_rules! impl_bit_op {
    ($trait:ident, $method:ident, $operator:tt) => {
        impl $trait for BitBoard {
            type Output = Self;

            fn $method(self, rhs: Self) -> Self::Output {
                Self(self.0 $operator rhs.0)
            }
        }
    };
}

macro_rules! impl_bit_assign_op {
    ($trait:ident, $method:ident, $operator:tt) => {
        impl $trait for BitBoard {
            fn $method(&mut self, rhs: Self) {
                self.0 $operator rhs.0;
            }
        }
    };
}

impl_bit_op!(BitAnd, bitand, &);
impl_bit_op!(BitOr, bitor, |);
impl_bit_op!(BitXor, bitxor, ^);
impl_bit_assign_op!(BitAndAssign, bitand_assign, &=);
impl_bit_assign_op!(BitOrAssign, bitor_assign, |=);
impl_bit_assign_op!(BitXorAssign, bitxor_assign, ^=);

impl Not for BitBoard {
    type Output = Self;

    fn not(self) -> Self::Output {
        Self(!self.0)
    }
}

impl Sub for BitBoard {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self::Output {
        Self(self.0 & !rhs.0)
    }
}

impl SubAssign for BitBoard {
    fn sub_assign(&mut self, rhs: Self) {
        self.0 &= !rhs.0;
    }
}

impl Shl<u32> for BitBoard {
    type Output = Self;

    fn shl(self, amount: u32) -> Self::Output {
        self.shift_left(amount)
    }
}

impl ShlAssign<u32> for BitBoard {
    fn shl_assign(&mut self, amount: u32) {
        *self = self.shift_left(amount);
    }
}

impl Shr<u32> for BitBoard {
    type Output = Self;

    fn shr(self, amount: u32) -> Self::Output {
        self.shift_right(amount)
    }
}

impl ShrAssign<u32> for BitBoard {
    fn shr_assign(&mut self, amount: u32) {
        *self = self.shift_right(amount);
    }
}

/// An iterator over the squares contained in a [`BitBoard`].
#[derive(Clone, Debug)]
pub struct Squares {
    bits: u64,
}

impl Iterator for Squares {
    type Item = Square;

    fn next(&mut self) -> Option<Self::Item> {
        if self.bits == 0 {
            return None;
        }
        let index = self.bits.trailing_zeros() as u8;
        self.bits &= self.bits - 1;
        Square::from_index(index)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.bits.count_ones() as usize;
        (remaining, Some(remaining))
    }
}

impl DoubleEndedIterator for Squares {
    fn next_back(&mut self) -> Option<Self::Item> {
        if self.bits == 0 {
            return None;
        }
        let index = (63 - self.bits.leading_zeros()) as u8;
        self.bits &= !(1_u64 << index);
        Square::from_index(index)
    }
}

impl ExactSizeIterator for Squares {}
impl FusedIterator for Squares {}
