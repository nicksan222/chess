use core::fmt;

use super::{Color, Square};

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

/// A chess piece with its color, movement kind, and current square.
///
/// Pieces are self-locating domain objects. A position owns the set of pieces
/// and preserves the invariant that no two pieces share a square.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Piece {
    color: Color,
    kind: PieceKind,
    square: Square,
}

impl Piece {
    /// Creates a piece at `square`.
    #[must_use]
    pub const fn new(color: Color, kind: PieceKind, square: Square) -> Self {
        Self {
            color,
            kind,
            square,
        }
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

    /// Returns the piece's current square.
    #[must_use]
    pub const fn square(self) -> Square {
        self.square
    }

    /// Returns every currently legal destination for this piece.
    #[must_use]
    pub fn where_can_move(self, board: &crate::Board) -> crate::SquareSet {
        board.destinations(self)
    }

    pub(crate) const fn at(self, square: Square) -> Self {
        Self { square, ..self }
    }

    pub(crate) const fn promoted(self, kind: PieceKind) -> Self {
        Self { kind, ..self }
    }
}
