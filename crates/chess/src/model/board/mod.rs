mod pieces;
mod state;

pub use pieces::BoardPieces;
pub use state::{CastlingRights, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber};

use super::{Color, Piece, PieceKind, Square, SquareSet};
use pieces::initial_pieces;

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
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.pieces[square.index().value() as usize]
    }

    /// Returns all squares occupied by pieces matching `color` and `kind`.
    #[must_use]
    pub fn pieces(&self, color: Color, kind: PieceKind) -> SquareSet {
        self.iter()
            .filter_map(|(square, piece)| {
                (piece.color() == color && piece.kind() == kind).then_some(square)
            })
            .collect()
    }

    /// Returns all squares occupied by `color`.
    #[must_use]
    pub fn occupied_by(&self, color: Color) -> SquareSet {
        self.iter()
            .filter_map(|(square, piece)| (piece.color() == color).then_some(square))
            .collect()
    }

    /// Returns every occupied square.
    #[must_use]
    pub fn occupied(&self) -> SquareSet {
        self.iter().map(|(square, _)| square).collect()
    }

    /// Places `piece` at its own square, returning the previous occupant.
    pub fn set_piece(&mut self, piece: Piece) -> Option<Piece> {
        let slot = &mut self.pieces[piece.square().index().value() as usize];
        let previous = *slot;
        *slot = Some(piece);
        previous
    }

    /// Removes and returns the piece on `square`.
    pub fn remove_piece(&mut self, square: Square) -> Option<Piece> {
        self.pieces[square.index().value() as usize].take()
    }

    /// Returns occupied squares and their self-locating pieces in board order.
    pub fn iter(&self) -> BoardPieces<'_> {
        BoardPieces::new(self, self.occupied_count())
    }

    fn occupied_count(&self) -> usize {
        self.pieces.iter().filter(|piece| piece.is_some()).count()
    }

    /// Returns the player whose turn it is.
    #[must_use]
    pub const fn side_to_move(&self) -> Color {
        self.side_to_move
    }

    /// Sets the player whose turn it is.
    pub fn set_side_to_move(&mut self, color: Color) {
        self.side_to_move = color;
    }

    /// Returns the retained castling rights.
    #[must_use]
    pub const fn castling_rights(&self) -> CastlingRights {
        self.castling_rights
    }

    /// Replaces the retained castling rights.
    pub fn set_castling_rights(&mut self, rights: CastlingRights) {
        self.castling_rights = rights;
    }

    /// Returns the en-passant target square, when one is available.
    #[must_use]
    pub const fn en_passant_target(&self) -> Option<Square> {
        self.en_passant_target
    }

    /// Replaces the en-passant target square.
    pub fn set_en_passant_target(&mut self, target: Option<Square>) {
        self.en_passant_target = target;
    }

    /// Returns the number of halfmoves since a pawn move or capture.
    #[must_use]
    pub const fn halfmove_clock(&self) -> HalfmoveClock {
        self.halfmove_clock
    }

    /// Replaces the halfmove clock.
    pub fn set_halfmove_clock(&mut self, clock: HalfmoveClock) {
        self.halfmove_clock = clock;
    }

    /// Returns the one-based fullmove number.
    #[must_use]
    pub const fn fullmove_number(&self) -> FullmoveNumber {
        self.fullmove_number
    }

    /// Replaces the validated fullmove number.
    pub fn set_fullmove_number(&mut self, number: FullmoveNumber) {
        self.fullmove_number = number;
    }
}
