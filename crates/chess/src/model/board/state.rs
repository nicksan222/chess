use core::{fmt, num::NonZeroU32};

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

/// The error returned when fullmove number zero is requested.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidFullmoveNumber;

impl fmt::Display for InvalidFullmoveNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("fullmove number must be at least one")
    }
}

impl core::error::Error for InvalidFullmoveNumber {}
