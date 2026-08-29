//! Forsyth–Edwards Notation primitives.
//!
//! Position-level FEN parsing can build on these conversions without coupling
//! notation details to domain values.

use core::fmt;

use crate::{Color, Piece, PieceKind};

/// Encodes a piece as its single-character FEN symbol.
///
/// White pieces are uppercase and black pieces are lowercase.
#[must_use]
pub const fn encode_piece(piece: Piece) -> char {
    match (piece.color(), piece.kind()) {
        (Color::White, PieceKind::Pawn) => 'P',
        (Color::White, PieceKind::Knight) => 'N',
        (Color::White, PieceKind::Bishop) => 'B',
        (Color::White, PieceKind::Rook) => 'R',
        (Color::White, PieceKind::Queen) => 'Q',
        (Color::White, PieceKind::King) => 'K',
        (Color::Black, PieceKind::Pawn) => 'p',
        (Color::Black, PieceKind::Knight) => 'n',
        (Color::Black, PieceKind::Bishop) => 'b',
        (Color::Black, PieceKind::Rook) => 'r',
        (Color::Black, PieceKind::Queen) => 'q',
        (Color::Black, PieceKind::King) => 'k',
    }
}

/// Decodes one single-character FEN piece symbol.
pub const fn decode_piece(symbol: char) -> Result<Piece, PieceSymbolError> {
    let piece = match symbol {
        'P' => Piece::new(Color::White, PieceKind::Pawn),
        'N' => Piece::new(Color::White, PieceKind::Knight),
        'B' => Piece::new(Color::White, PieceKind::Bishop),
        'R' => Piece::new(Color::White, PieceKind::Rook),
        'Q' => Piece::new(Color::White, PieceKind::Queen),
        'K' => Piece::new(Color::White, PieceKind::King),
        'p' => Piece::new(Color::Black, PieceKind::Pawn),
        'n' => Piece::new(Color::Black, PieceKind::Knight),
        'b' => Piece::new(Color::Black, PieceKind::Bishop),
        'r' => Piece::new(Color::Black, PieceKind::Rook),
        'q' => Piece::new(Color::Black, PieceKind::Queen),
        'k' => Piece::new(Color::Black, PieceKind::King),
        _ => return Err(PieceSymbolError { symbol }),
    };
    Ok(piece)
}

/// An invalid FEN piece symbol.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PieceSymbolError {
    symbol: char,
}

impl PieceSymbolError {
    /// Returns the rejected symbol.
    #[must_use]
    pub const fn symbol(self) -> char {
        self.symbol
    }
}

impl fmt::Display for PieceSymbolError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "'{}' is not a FEN piece symbol", self.symbol)
    }
}

impl core::error::Error for PieceSymbolError {}
