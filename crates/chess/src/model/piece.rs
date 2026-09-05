//! Piece kinds and self-locating piece values.

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

    /// Piece kinds a pawn may promote to.
    pub const PROMOTIONS: [Self; 4] = [Self::Knight, Self::Bishop, Self::Rook, Self::Queen];
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
/// Pieces are self-locating domain objects. A [`crate::Board`] owns the set
/// of pieces and preserves the invariant that no two pieces share a square.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Piece {
    color: Color,
    kind: PieceKind,
    square: Square,
}

impl Piece {
    /// Creates a piece at `square`.
    ///
    /// Combines a [`Color`], a [`PieceKind`], and the square the piece
    /// occupies. A [`Board`](crate::Board) preserves the invariant that
    /// no two pieces share a square; placing two pieces on one square
    /// keeps only the last write.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Color, Piece, PieceKind, Square};
    ///
    /// let piece = Piece::new(Color::White, PieceKind::Knight, Square::G1);
    /// assert_eq!(piece.square(), Square::G1);
    /// ```
    #[must_use]
    pub const fn new(color: Color, kind: PieceKind, square: Square) -> Self {
        Self {
            color,
            kind,
            square,
        }
    }

    /// Returns the piece's color.
    ///
    /// Reports which side owns the piece (White or Black).
    #[must_use]
    pub const fn color(self) -> Color {
        self.color
    }

    /// Returns the piece's movement kind.
    ///
    /// Reports the movement category (pawn through king), independent of
    /// color. See [`PieceKind`].
    #[must_use]
    pub const fn kind(self) -> PieceKind {
        self.kind
    }

    /// Returns the piece's current square.
    ///
    /// Pieces are self-locating: this square selects the piece's slot in
    /// a [`Board`](crate::Board).
    #[must_use]
    pub const fn square(self) -> Square {
        self.square
    }

    /// Moves a piece copy to `square` without changing kind or color.
    ///
    /// Used when deriving the next position; the original value is left
    /// unchanged because [`Piece`] is `Copy`.
    pub(crate) const fn at(self, square: Square) -> Self {
        Self { square, ..self }
    }

    /// Returns a copy of this piece with movement kind `kind`.
    ///
    /// Used to apply a promotion result; the color and square are
    /// preserved. Callers pass only knight, bishop, rook, or queen (see
    /// [`PieceKind::PROMOTIONS`]).
    pub(crate) const fn promoted(self, kind: PieceKind) -> Self {
        Self { kind, ..self }
    }
}
