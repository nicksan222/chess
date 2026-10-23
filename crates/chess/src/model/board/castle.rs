//! The four castling maneuvers and the squares they involve.

use crate::{Color, Square};

/// The wing a king castles toward.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CastleSide {
    /// Toward the `h` file.
    Kingside,
    /// Toward the `a` file.
    Queenside,
}

/// One of the four castling maneuvers: a color castling toward a wing.
///
/// This is the single lookup for castling geometry. Rook relocation, rights
/// revocation and engine-move conversion all derive from it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct Castle {
    color: Color,
    side: CastleSide,
}

impl Castle {
    /// Every castling maneuver.
    pub(crate) const ALL: [Self; 4] = [
        Self::new(Color::White, CastleSide::Kingside),
        Self::new(Color::White, CastleSide::Queenside),
        Self::new(Color::Black, CastleSide::Kingside),
        Self::new(Color::Black, CastleSide::Queenside),
    ];

    pub(crate) const fn new(color: Color, side: CastleSide) -> Self {
        Self { color, side }
    }

    /// Returns the castling maneuver a king move from `from` to `to` makes.
    pub(crate) fn from_king_move(from: Square, to: Square) -> Option<Self> {
        Self::ALL
            .into_iter()
            .find(|castle| castle.king_move() == (from, to))
    }

    /// Returns the maneuver whose rook starts on `square`, if `color` owns it.
    pub(crate) fn from_rook_origin(color: Color, square: Square) -> Option<Self> {
        Self::ALL
            .into_iter()
            .find(|castle| castle.color == color && castle.rook_move().0 == square)
    }

    pub(crate) const fn color(self) -> Color {
        self.color
    }

    pub(crate) const fn side(self) -> CastleSide {
        self.side
    }

    /// Returns the king's origin and destination.
    pub(crate) const fn king_move(self) -> (Square, Square) {
        match (self.color, self.side) {
            (Color::White, CastleSide::Kingside) => (Square::E1, Square::G1),
            (Color::White, CastleSide::Queenside) => (Square::E1, Square::C1),
            (Color::Black, CastleSide::Kingside) => (Square::E8, Square::G8),
            (Color::Black, CastleSide::Queenside) => (Square::E8, Square::C8),
        }
    }

    /// Returns the rook's origin and destination.
    pub(crate) const fn rook_move(self) -> (Square, Square) {
        match (self.color, self.side) {
            (Color::White, CastleSide::Kingside) => (Square::H1, Square::F1),
            (Color::White, CastleSide::Queenside) => (Square::A1, Square::D1),
            (Color::Black, CastleSide::Kingside) => (Square::H8, Square::F8),
            (Color::Black, CastleSide::Queenside) => (Square::A8, Square::D8),
        }
    }
}
