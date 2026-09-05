//! Ordered iteration over self-locating board pieces.

use core::iter::FusedIterator;

use crate::{AllSquares, Piece, Square};

use super::Board;

/// An iterator over the self-locating pieces in a [`Board`].
#[derive(Clone, Debug)]
pub struct BoardPieces<'a> {
    board: &'a Board,
    squares: AllSquares,
    remaining: usize,
}

impl<'a> BoardPieces<'a> {
    /// Creates an iterator over the pieces in `board`.
    ///
    /// `remaining` must equal the number of occupied squares; it backs
    /// the [`ExactSizeIterator`] length. Yields [`Piece`] values in
    /// board-index order (`a1` through `h8`) and borrows the board for
    /// `'a`. Prefer [`Board::pieces`] or `&board.into_iter()`, which
    /// compute the count automatically.
    pub(super) fn new(board: &'a Board, remaining: usize) -> Self {
        Self {
            board,
            squares: Square::all(),
            remaining,
        }
    }
}

impl Iterator for BoardPieces<'_> {
    type Item = Piece;

    fn next(&mut self) -> Option<Self::Item> {
        for square in self.squares.by_ref() {
            if let Some(piece) = self.board.piece_at(square) {
                self.remaining -= 1;
                return Some(piece);
            }
        }
        None
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.remaining, Some(self.remaining))
    }
}

impl DoubleEndedIterator for BoardPieces<'_> {
    fn next_back(&mut self) -> Option<Self::Item> {
        while let Some(square) = self.squares.next_back() {
            if let Some(piece) = self.board.piece_at(square) {
                self.remaining -= 1;
                return Some(piece);
            }
        }
        None
    }
}

impl ExactSizeIterator for BoardPieces<'_> {}
impl FusedIterator for BoardPieces<'_> {}

impl<'a> IntoIterator for &'a Board {
    type Item = Piece;
    type IntoIter = BoardPieces<'a>;

    fn into_iter(self) -> Self::IntoIter {
        self.pieces()
    }
}
