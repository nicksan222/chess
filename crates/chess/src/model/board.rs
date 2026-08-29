use core::{fmt, iter::FusedIterator, num::NonZeroU32};

use super::{Color, Piece, PieceKind, Rank, Square, SquareSet};

const fn initial_pieces() -> [Option<Piece>; Square::COUNT] {
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

/// The castling options retained by a board.
#[derive(Clone, Copy, Default, PartialEq, Eq, Hash)]
#[repr(transparent)]
pub struct CastlingRights(u8);

impl CastlingRights {
    const WHITE_KINGSIDE: u8 = 1 << 0;
    const WHITE_QUEENSIDE: u8 = 1 << 1;
    const BLACK_KINGSIDE: u8 = 1 << 2;
    const BLACK_QUEENSIDE: u8 = 1 << 3;

    /// No castling rights.
    pub const NONE: Self = Self(0);

    /// Every initial castling right.
    pub const ALL: Self = Self(
        Self::WHITE_KINGSIDE | Self::WHITE_QUEENSIDE | Self::BLACK_KINGSIDE | Self::BLACK_QUEENSIDE,
    );

    const fn mask(color: Color, kingside: bool) -> u8 {
        match (color, kingside) {
            (Color::White, true) => Self::WHITE_KINGSIDE,
            (Color::White, false) => Self::WHITE_QUEENSIDE,
            (Color::Black, true) => Self::BLACK_KINGSIDE,
            (Color::Black, false) => Self::BLACK_QUEENSIDE,
        }
    }

    /// Returns whether `color` may castle on the king's side.
    #[must_use]
    pub const fn kingside(self, color: Color) -> bool {
        self.0 & Self::mask(color, true) != 0
    }

    /// Returns whether `color` may castle on the queen's side.
    #[must_use]
    pub const fn queenside(self, color: Color) -> bool {
        self.0 & Self::mask(color, false) != 0
    }

    /// Adds or removes the king-side right for `color`.
    pub fn set_kingside(&mut self, color: Color, allowed: bool) {
        self.set(Self::mask(color, true), allowed);
    }

    /// Adds or removes the queen-side right for `color`.
    pub fn set_queenside(&mut self, color: Color, allowed: bool) {
        self.set(Self::mask(color, false), allowed);
    }

    /// Removes both castling rights for `color`.
    pub fn clear(&mut self, color: Color) {
        self.set_kingside(color, false);
        self.set_queenside(color, false);
    }

    fn set(&mut self, mask: u8, enabled: bool) {
        if enabled {
            self.0 |= mask;
        } else {
            self.0 &= !mask;
        }
    }
}

impl fmt::Debug for CastlingRights {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut set = formatter.debug_set();
        for color in Color::ALL {
            if self.kingside(color) {
                set.entry(&(color, "kingside"));
            }
            if self.queenside(color) {
                set.entry(&(color, "queenside"));
            }
        }
        set.finish()
    }
}

/// The number of halfmoves since the last pawn move or capture.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct HalfmoveClock(u32);

impl HalfmoveClock {
    /// A reset halfmove clock.
    pub const ZERO: Self = Self(0);

    /// Creates a halfmove clock at an input or persistence boundary.
    #[must_use]
    pub const fn new(value: u32) -> Self {
        Self(value)
    }

    /// Returns the primitive representation for serialization.
    #[must_use]
    pub const fn value(self) -> u32 {
        self.0
    }

    pub(crate) fn increment(&mut self) {
        self.0 = self.0.saturating_add(1);
    }
}

impl fmt::Display for HalfmoveClock {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

/// A one-based fullmove number.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct FullmoveNumber(NonZeroU32);

impl FullmoveNumber {
    /// The first fullmove.
    pub const ONE: Self = Self(NonZeroU32::MIN);

    /// Creates a validated one-based fullmove number.
    pub const fn new(value: u32) -> Result<Self, InvalidFullmoveNumber> {
        match NonZeroU32::new(value) {
            Some(value) => Ok(Self(value)),
            None => Err(InvalidFullmoveNumber),
        }
    }

    /// Returns the primitive representation for serialization.
    #[must_use]
    pub const fn value(self) -> u32 {
        self.0.get()
    }

    pub(crate) fn increment(&mut self) {
        if let Some(next) = self.0.get().checked_add(1).and_then(NonZeroU32::new) {
            self.0 = next;
        }
    }
}

impl fmt::Display for FullmoveNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

impl TryFrom<u32> for FullmoveNumber {
    type Error = InvalidFullmoveNumber;

    fn try_from(value: u32) -> Result<Self, Self::Error> {
        Self::new(value)
    }
}

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
        BoardPieces {
            board: self,
            squares: Square::all(),
            remaining: self.occupied_count(),
        }
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

    pub(crate) fn finish_move(&mut self, moved: Piece, captured: Option<Piece>, double_push: bool) {
        if moved.kind() == PieceKind::Pawn || captured.is_some() {
            self.halfmove_clock = HalfmoveClock::ZERO;
        } else {
            self.halfmove_clock.increment();
        }
        self.en_passant_target = if double_push {
            let rank_delta = match moved.color() {
                Color::White => 1,
                Color::Black => -1,
            };
            moved
                .square()
                .offset(super::SquareOffset::new(0, rank_delta))
        } else {
            None
        };
        if moved.color() == Color::Black {
            self.fullmove_number.increment();
        }
        self.side_to_move = moved.color().opposite();
    }

    pub(crate) fn is_back_rank(square: Square, color: Color) -> bool {
        square.rank()
            == match color {
                Color::White => Rank::Eight,
                Color::Black => Rank::One,
            }
    }
}

/// The error returned when fullmove number zero is requested.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidFullmoveNumber;

impl fmt::Display for InvalidFullmoveNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("fullmove number must be at least one")
    }
}

impl core::error::Error for InvalidFullmoveNumber {}

/// An iterator over the occupied squares in a [`Board`].
#[derive(Clone, Debug)]
pub struct BoardPieces<'a> {
    board: &'a Board,
    squares: super::AllSquares,
    remaining: usize,
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
