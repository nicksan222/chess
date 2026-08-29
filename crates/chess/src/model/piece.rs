use core::fmt;

use super::Color;

/// The movement category of a chess piece, independent of color.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum PieceKind {
    /// A pawn.
    Pawn,
    /// A knight.
    Knight,
    /// A bishop.
    Bishop,
    /// A rook.
    Rook,
    /// A queen.
    Queen,
    /// A king.
    King,
}

impl PieceKind {
    /// Every piece kind in pawn-through-king order.
    pub const ALL: [Self; 6] = [
        Self::Pawn,
        Self::Knight,
        Self::Bishop,
        Self::Rook,
        Self::Queen,
        Self::King,
    ];
}

impl fmt::Display for PieceKind {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Pawn => "pawn",
            Self::Knight => "knight",
            Self::Bishop => "bishop",
            Self::Rook => "rook",
            Self::Queen => "queen",
            Self::King => "king",
        })
    }
}

/// A chess piece identified by color and movement kind.
///
/// A piece is an immutable domain value. Its notation and movement behavior
/// belong to notation and position-level modules respectively.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Piece {
    color: Color,
    kind: PieceKind,
}

impl Piece {
    /// Creates a piece.
    #[must_use]
    pub const fn new(color: Color, kind: PieceKind) -> Self {
        Self { color, kind }
    }

    /// Returns the piece's color.
    #[must_use]
    pub const fn color(self) -> Color {
        self.color
    }

    /// Returns the piece's movement kind.
    #[must_use]
    pub const fn kind(self) -> PieceKind {
        self.kind
    }
}
