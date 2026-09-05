//! Complete board state required to continue a chess game.

mod castling;
mod clocks;
mod iter;
mod setup;

pub use castling::CastlingRights;
pub use clocks::{FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber};
pub use iter::BoardPieces;

use super::{Color, Piece, PieceKind, Square, SquareSet};
use setup::initial_pieces;

/// A complete chess board, independent of move history and notation.
///
/// Every stored [`Piece`] owns its square. The remaining values are the state
/// needed to continue a game.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Board {
    pieces: [Option<Piece>; Square::COUNT],
    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant_target: Option<Square>,
    halfmove_clock: HalfmoveClock,
    fullmove_number: FullmoveNumber,
}

impl Board {
    /// The standard initial chess board.
    pub const INITIAL: Self = Self {
        pieces: initial_pieces(),
        side_to_move: Color::White,
        castling_rights: CastlingRights::ALL,
        en_passant_target: None,
        halfmove_clock: HalfmoveClock::ZERO,
        fullmove_number: FullmoveNumber::ONE,
    };

    /// Creates an empty board with White to move and move number one.
    ///
    /// The piece map is empty, no castling rights are retained, there is
    /// no en-passant target, the [`HalfmoveClock`] is zero, and the
    /// [`FullmoveNumber`] is one. Use [`Board::from_pieces`] to populate
    /// the board afterwards.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::Board;
    ///
    /// let board = Board::empty();
    /// assert!(board.occupied().is_empty());
    /// ```
    #[must_use]
    pub const fn empty() -> Self {
        Self {
            pieces: [None; Square::COUNT],
            side_to_move: Color::White,
            castling_rights: CastlingRights::NONE,
            en_passant_target: None,
            halfmove_clock: HalfmoveClock::ZERO,
            fullmove_number: FullmoveNumber::ONE,
        }
    }

    /// Returns the piece occupying `square`.
    ///
    /// Returns `None` when the square is empty. The returned [`Piece`]
    /// is self-locating, so its [`Square`](crate::Square) always equals
    /// `square`.
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.pieces[square.index().value() as usize]
    }

    /// Returns all squares occupied by pieces matching `color` and `kind`.
    ///
    /// Scans the board in index order (`a1` through `h8`) and collects
    /// every matching piece square into a [`SquareSet`]. Returns an empty
    /// set when no piece matches.
    #[must_use]
    pub fn occupied_by_kind(&self, color: Color, kind: PieceKind) -> SquareSet {
        self.iter()
            .filter(|piece| piece.color() == color && piece.kind() == kind)
            .map(Piece::square)
            .collect()
    }

    /// Returns all squares occupied by `color`.
    ///
    /// Scans the board in index order and collects every square holding
    /// a piece of `color` into a [`SquareSet`]. Returns an empty set when
    /// `color` has no pieces on the board.
    #[must_use]
    pub fn occupied_by(&self, color: Color) -> SquareSet {
        self.iter()
            .filter(|piece| piece.color() == color)
            .map(Piece::square)
            .collect()
    }

    /// Returns every occupied square.
    ///
    /// Collects the square of each stored [`Piece`] in board-index order
    /// into a [`SquareSet`]. Returns an empty set on [`Board::empty`].
    #[must_use]
    pub fn occupied(&self) -> SquareSet {
        self.iter().map(Piece::square).collect()
    }

    /// Places `piece` at its own square, returning the previous occupant.
    ///
    /// The piece carries its destination: only `piece.square()` selects
    /// the slot. When several pieces share a square, the last write wins;
    /// callers establishing a position (see [`Board::from_pieces`]) must
    /// therefore avoid duplicates unless replacement is intended.
    pub fn set_piece(&mut self, piece: Piece) -> Option<Piece> {
        let slot = &mut self.pieces[piece.square().index().value() as usize];
        let previous = *slot;
        *slot = Some(piece);
        previous
    }

    /// Removes and returns the piece on `square`.
    ///
    /// Returns `None` and leaves the board unchanged when `square` is
    /// already empty.
    pub fn remove_piece(&mut self, square: Square) -> Option<Piece> {
        self.pieces[square.index().value() as usize].take()
    }

    /// Returns self-locating pieces in board order.
    ///
    /// Yields each stored [`Piece`] from `a1` through `h8`. The iterator
    /// length equals the occupied-square count, so it is empty on
    /// [`Board::empty`]. Prefer [`Board::iter`] for generic iteration.
    pub fn pieces(&self) -> BoardPieces<'_> {
        BoardPieces::new(self, self.occupied_count())
    }

    /// Returns self-locating pieces in board order.
    ///
    /// An alias for [`Board::pieces`] so `&Board` works with generic
    /// `IntoIterator` and iterator-adapter code.
    pub fn iter(&self) -> BoardPieces<'_> {
        self.pieces()
    }

    fn occupied_count(&self) -> usize {
        self.pieces.iter().filter(|piece| piece.is_some()).count()
    }

    /// Returns the player whose turn it is.
    ///
    /// This records only whose move is next; it carries no legality or
    /// check information.
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.side_to_move
    }

    /// Sets the player whose turn it is.
    ///
    /// Overwrites the previous side to move without touching pieces,
    /// clocks, or rights.
    pub fn set_side_to_move(&mut self, color: Color) {
        self.side_to_move = color;
    }

    /// Returns the retained castling rights.
    ///
    /// The [`CastlingRights`] value records only which rights are still
    /// retained; it does not verify that the king and rook are placed or
    /// that the path is legal.
    #[must_use]
    pub const fn castling_rights(&self) -> CastlingRights {
        self.castling_rights
    }

    /// Replaces the retained castling rights.
    ///
    /// Overwrites the whole [`CastlingRights`] bitmask. To adjust one
    /// side, read the rights, mutate the copy, then store it back.
    pub fn set_castling_rights(&mut self, rights: CastlingRights) {
        self.castling_rights = rights;
    }

    /// Returns the en-passant target square, when one is available.
    ///
    /// This is the capturable destination square behind a pawn that just
    /// advanced two squares, or `None` when no en-passant capture is
    /// available. It never indicates which pawn moved.
    #[must_use]
    pub const fn en_passant_target(&self) -> Option<Square> {
        self.en_passant_target
    }

    /// Replaces the en-passant target square.
    ///
    /// Pass `None` to clear the target. The setter stores the square
    /// verbatim and does not validate that a double pawn push produced it.
    pub fn set_en_passant_target(&mut self, target: Option<Square>) {
        self.en_passant_target = target;
    }

    /// Returns the number of halfmoves since a pawn move or capture.
    ///
    /// The count is measured in halfmoves (plies) and is used with the
    /// fifty-move rule. See [`HalfmoveClock`].
    #[must_use]
    pub const fn halfmove_clock(&self) -> HalfmoveClock {
        self.halfmove_clock
    }

    /// Replaces the halfmove clock.
    ///
    /// Overwrites the [`HalfmoveClock`] verbatim without validating it
    /// against the pieces on the board.
    pub fn set_halfmove_clock(&mut self, clock: HalfmoveClock) {
        self.halfmove_clock = clock;
    }

    /// Returns the one-based fullmove number.
    ///
    /// The number starts at one and increments after Black's move. See
    /// [`FullmoveNumber`].
    #[must_use]
    pub const fn fullmove_number(&self) -> FullmoveNumber {
        self.fullmove_number
    }

    /// Replaces the validated fullmove number.
    ///
    /// Accepts only a pre-validated [`FullmoveNumber`] (values of at least
    /// one), so this setter itself cannot fail.
    pub fn set_fullmove_number(&mut self, number: FullmoveNumber) {
        self.fullmove_number = number;
    }
}
