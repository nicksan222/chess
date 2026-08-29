use core::iter::FusedIterator;

use crate::{AllSquares, Color, Piece, PieceKind, Square};

use super::Board;

pub(super) const fn initial_pieces() -> [Option<Piece>; Square::COUNT] {
    let mut pieces = [None; Square::COUNT];
    let back_rank = [
        PieceKind::Rook,
        PieceKind::Knight,
        PieceKind::Bishop,
        PieceKind::Queen,
        PieceKind::King,
        PieceKind::Bishop,
        PieceKind::Knight,
        PieceKind::Rook,
    ];
    let mut file = 0_u8;
    while file < 8 {
        let white_back = Square::from_raw_index_unchecked(file);
        let white_pawn = Square::from_raw_index_unchecked(8 + file);
        let black_pawn = Square::from_raw_index_unchecked(48 + file);
        let black_back = Square::from_raw_index_unchecked(56 + file);
        pieces[white_back.index().value() as usize] = Some(Piece::new(
            Color::White,
            back_rank[file as usize],
            white_back,
        ));
        pieces[white_pawn.index().value() as usize] =
            Some(Piece::new(Color::White, PieceKind::Pawn, white_pawn));
        pieces[black_pawn.index().value() as usize] =
            Some(Piece::new(Color::Black, PieceKind::Pawn, black_pawn));
        pieces[black_back.index().value() as usize] = Some(Piece::new(
            Color::Black,
            back_rank[file as usize],
            black_back,
        ));
        file += 1;
    }
    pieces
}

/// An iterator over the occupied squares in a [`Board`].
#[derive(Clone, Debug)]
pub struct BoardPieces<'a> {
    board: &'a Board,
    squares: AllSquares,
    remaining: usize,
}

impl<'a> BoardPieces<'a> {
    pub(super) fn new(board: &'a Board, remaining: usize) -> Self {
        Self {
            board,
            squares: Square::all(),
            remaining,
        }
    }
}

impl Iterator for BoardPieces<'_> {
    type Item = (Square, Piece);

    fn next(&mut self) -> Option<Self::Item> {
        for square in self.squares.by_ref() {
            if let Some(piece) = self.board.piece_at(square) {
                self.remaining -= 1;
                return Some((square, piece));
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
                return Some((square, piece));
            }
        }
        None
    }
}

impl ExactSizeIterator for BoardPieces<'_> {}
impl FusedIterator for BoardPieces<'_> {}
