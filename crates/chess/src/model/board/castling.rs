//! Compact representation and mutation of castling rights.

use core::fmt;

use crate::Color;

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

    /// Grants the king-side right for `color`.
    pub fn grant_kingside(&mut self, color: Color) {
        self.set(Self::mask(color, true), true);
    }

    /// Revokes the king-side right for `color`.
    pub fn revoke_kingside(&mut self, color: Color) {
        self.set(Self::mask(color, true), false);
    }

    /// Grants the queen-side right for `color`.
    pub fn grant_queenside(&mut self, color: Color) {
        self.set(Self::mask(color, false), true);
    }

    /// Revokes the queen-side right for `color`.
    pub fn revoke_queenside(&mut self, color: Color) {
        self.set(Self::mask(color, false), false);
    }

    /// Removes both castling rights for `color`.
    pub fn clear(&mut self, color: Color) {
        self.revoke_kingside(color);
        self.revoke_queenside(color);
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
