//! Coordinate move intent and promotion values.

mod parse;

pub use parse::ParseMoveError;

use core::fmt;

use super::{PieceKind, Square};

/// A chess move's origin, destination, and optional promotion.
///
/// This value records move intent. Whether a move is legal in a particular
/// board belongs to move generation and game-state validation.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ChessMove {
    from: Square,
    to: Square,
    promotion: Option<PieceKind>,
}

impl ChessMove {
    /// Creates a move without promotion.
    ///
    /// Records the origin `from` and destination `to` squares. Squares
    /// may be equal or otherwise pseudo-legal here: legality against a
    /// [`Board`](crate::Board) belongs to move generation, not to this
    /// constructor.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Square};
    ///
    /// let mv = ChessMove::new(Square::E2, Square::E4);
    /// assert_eq!(mv.promotion_kind(), None);
    /// ```
    #[must_use]
    pub const fn new(from: Square, to: Square) -> Self {
        Self {
            from,
            to,
            promotion: None,
        }
    }

    /// Creates a promotion move.
    ///
    /// Pawns may promote only to a knight, bishop, rook, or queen.
    ///
    /// The move records intent only; it does not check that `from` holds
    /// a pawn or that `to` sits on the final rank.
    ///
    /// # Errors
    ///
    /// Returns [`InvalidPromotion`] when `kind` is a pawn or a king.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, PieceKind, Square};
    ///
    /// let mv = ChessMove::promotion(Square::E7, Square::E8, PieceKind::Queen)?;
    /// assert_eq!(mv.promotion_kind(), Some(PieceKind::Queen));
    /// # Ok::<(), chess::InvalidPromotion>(())
    /// ```
    pub const fn promotion(
        from: Square,
        to: Square,
        kind: PieceKind,
    ) -> Result<Self, InvalidPromotion> {
        match kind {
            PieceKind::Knight | PieceKind::Bishop | PieceKind::Rook | PieceKind::Queen => {
                Ok(Self {
                    from,
                    to,
                    promotion: Some(kind),
                })
            }
            PieceKind::Pawn | PieceKind::King => Err(InvalidPromotion { kind }),
        }
    }

    /// Returns the move's origin square.
    ///
    /// This is the square the moving piece leaves, as recorded at
    /// construction or parsing time.
    #[must_use]
    pub const fn from(self) -> Square {
        self.from
    }

    /// Returns the move's destination square.
    ///
    /// This is the square the moving piece enters, including the
    /// promotion square for promotion moves.
    #[must_use]
    pub const fn to(self) -> Square {
        self.to
    }

    /// Returns the requested promotion piece kind.
    ///
    /// Returns `None` for non-promotion moves and one of
    /// [`PieceKind::PROMOTIONS`] for promotion moves created with
    /// [`ChessMove::promotion`] or parsed with a trailing `n`, `b`, `r`,
    /// or `q`.
    #[must_use]
    pub const fn promotion_kind(self) -> Option<PieceKind> {
        self.promotion
    }

    /// Returns the compact promotion discriminant used by move encoding.
    ///
    /// Maps no promotion to `0` and knight, bishop, rook, queen to
    /// `1`–`4`. Unreachable pawn and king promotions map to `0` because
    /// [`ChessMove::promotion`] rejects them at construction.
    pub(crate) const fn promotion_code(self) -> u8 {
        match self.promotion {
            None => 0,
            Some(PieceKind::Knight) => 1,
            Some(PieceKind::Bishop) => 2,
            Some(PieceKind::Rook) => 3,
            Some(PieceKind::Queen) => 4,
            Some(PieceKind::Pawn | PieceKind::King) => 0,
        }
    }
}

impl fmt::Display for ChessMove {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}{}", self.from, self.to)?;
        if let Some(kind) = self.promotion {
            formatter.write_str(match kind {
                PieceKind::Knight => "n",
                PieceKind::Bishop => "b",
                PieceKind::Rook => "r",
                PieceKind::Queen => "q",
                PieceKind::Pawn | PieceKind::King => {
                    unreachable!("the promotion constructor rejects pawns and kings")
                }
            })?;
        }
        Ok(())
    }
}

/// The error returned for a pawn or king promotion target.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct InvalidPromotion {
    kind: PieceKind,
}

impl InvalidPromotion {
    /// Returns the rejected piece kind.
    ///
    /// The value is always [`PieceKind::Pawn`] or [`PieceKind::King`],
    /// the two targets [`ChessMove::promotion`] refuses.
    #[must_use]
    pub const fn kind(self) -> PieceKind {
        self.kind
    }
}

impl fmt::Display for InvalidPromotion {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "a pawn cannot promote to a {}", self.kind)
    }
}

impl_error!(InvalidPromotion);
