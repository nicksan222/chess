//! Collection conversions and set operators for square sets.

use core::ops::{
    BitAnd, BitAndAssign, BitOr, BitOrAssign, BitXor, BitXorAssign, Not, Sub, SubAssign,
};

use crate::Square;

use super::{SquareSet, Squares};

impl From<Square> for SquareSet {
    fn from(square: Square) -> Self {
        Self::from_square(square)
    }
}

impl FromIterator<Square> for SquareSet {
    fn from_iter<I: IntoIterator<Item = Square>>(iter: I) -> Self {
        let mut set = Self::EMPTY;
        set.extend(iter);
        set
    }
}

impl Extend<Square> for SquareSet {
    fn extend<I: IntoIterator<Item = Square>>(&mut self, iter: I) {
        for square in iter {
            self.insert(square);
        }
    }
}

impl<'a> Extend<&'a Square> for SquareSet {
    fn extend<I: IntoIterator<Item = &'a Square>>(&mut self, iter: I) {
        self.extend(iter.into_iter().copied());
    }
}

impl IntoIterator for SquareSet {
    type Item = Square;
    type IntoIter = Squares;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

impl IntoIterator for &SquareSet {
    type Item = Square;
    type IntoIter = Squares;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

macro_rules! impl_set_op {
    ($trait:ident, $method:ident, $operator:tt) => {
        impl $trait for SquareSet {
            type Output = Self;

            fn $method(self, rhs: Self) -> Self::Output {
                Self(self.0 $operator rhs.0)
            }
        }
    };
}

macro_rules! impl_set_assign_op {
    ($trait:ident, $method:ident, $operator:tt) => {
        impl $trait for SquareSet {
            fn $method(&mut self, rhs: Self) {
                self.0 $operator rhs.0;
            }
        }
    };
}

impl_set_op!(BitAnd, bitand, &);
impl_set_op!(BitOr, bitor, |);
impl_set_op!(BitXor, bitxor, ^);
impl_set_assign_op!(BitAndAssign, bitand_assign, &=);
impl_set_assign_op!(BitOrAssign, bitor_assign, |=);
impl_set_assign_op!(BitXorAssign, bitxor_assign, ^=);

impl Not for SquareSet {
    type Output = Self;

    fn not(self) -> Self::Output {
        Self(!self.0)
    }
}

impl Sub for SquareSet {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self::Output {
        Self(self.0 & !rhs.0)
    }
}

impl SubAssign for SquareSet {
    fn sub_assign(&mut self, rhs: Self) {
        self.0 &= !rhs.0;
    }
}
