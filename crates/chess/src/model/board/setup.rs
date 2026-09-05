//! Initial and caller-provided board construction.

use crate::{Color, Piece, PieceKind, Square};

use super::Board;

impl Board {
    /// Creates an otherwise empty board populated by self-locating pieces.
    ///
    /// If multiple pieces occupy the same square, the last one replaces the
    /// previous occupant.
    ///
    /// The board starts from [`Board::empty`], so side to move is White,
    /// castling rights are empty, and both clocks start at their initial
    /// values. Each [`Piece`] carries its own [`Square`](crate::Square),
    /// which selects the destination slot.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Board, Color, Piece, PieceKind, Square};
    ///
    /// let board = Board::from_pieces([
    ///     Piece::new(Color::White, PieceKind::King, Square::E1),
    ///     Piece::new(Color::Black, PieceKind::King, Square::E8),
    /// ]);
    /// assert_eq!(board.occupied().len().value(), 2);
    /// ```
    pub fn from_pieces(pieces: impl IntoIterator<Item = Piece>) -> Self {
        pieces.into_iter().collect()
    }
}

impl FromIterator<Piece> for Board {
    fn from_iter<I: IntoIterator<Item = Piece>>(pieces: I) -> Self {
        let mut board = Self::empty();
        board.extend(pieces);
        board
    }
}

impl Extend<Piece> for Board {
    fn extend<I: IntoIterator<Item = Piece>>(&mut self, pieces: I) {
        for piece in pieces {
            self.set_piece(piece);
        }
    }
}

impl<'a> Extend<&'a Piece> for Board {
    fn extend<I: IntoIterator<Item = &'a Piece>>(&mut self, pieces: I) {
        self.extend(pieces.into_iter().copied());
    }
}

/// Builds the standard initial piece placement in board-index order.
///
/// Returns a 64-slot array with White back rank and pawns on ranks 1–2
/// and Black pawns and back rank on ranks 7–8. Used by [`Board::INITIAL`].
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
