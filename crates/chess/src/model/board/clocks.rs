//! Validated halfmove and fullmove counters.

use core::{fmt, num::NonZeroU32};

/// The number of halfmoves since the last pawn move or capture.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct HalfmoveClock(u32);

impl HalfmoveClock {
    /// A reset halfmove clock.
    pub const ZERO: Self = Self(0);

    /// Creates a halfmove clock at an input or persistence boundary.
    ///
    /// Stores `value` verbatim as the number of halfmoves since the last
    /// pawn move or capture. Use this at parsing or deserialization
    /// boundaries; inside the engine the clock advances one halfmove at
    /// a time instead.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::HalfmoveClock;
    ///
    /// let clock = HalfmoveClock::new(4);
    /// assert_eq!(clock.value(), 4);
    /// ```
    #[must_use]
    pub const fn new(value: u32) -> Self {
        Self(value)
    }

    /// Returns the primitive halfmove count for serialization.
    ///
    /// The result is a plain halfmove (ply) count of `0` or more.
    #[must_use]
    pub const fn value(self) -> u32 {
        self.0
    }

    /// Advances the clock by one halfmove, saturating at `u32::MAX`.
    ///
    /// Saturating (rather than wrapping or panicking) keeps long
    /// degenerate sessions representable; reaching the maximum is not a
    /// realistic fifty-move-rule scenario.
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
    ///
    /// Fullmove numbers start at one and increment after Black's move.
    ///
    /// # Errors
    ///
    /// Returns [`InvalidFullmoveNumber`] when `value` is zero.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::FullmoveNumber;
    ///
    /// assert!(FullmoveNumber::new(1).is_ok());
    /// assert!(FullmoveNumber::new(0).is_err());
    /// ```
    pub const fn new(value: u32) -> Result<Self, InvalidFullmoveNumber> {
        match NonZeroU32::new(value) {
            Some(value) => Ok(Self(value)),
            None => Err(InvalidFullmoveNumber),
        }
    }

    /// Returns the primitive fullmove number for serialization.
    ///
    /// The result is always at least one.
    #[must_use]
    pub const fn value(self) -> u32 {
        self.0.get()
    }

    /// Advances the number by one fullmove, saturating at `u32::MAX`.
    ///
    /// Values that would overflow keep the current maximum instead of
    /// wrapping, so the one-based invariant is preserved.
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

impl_error!(InvalidFullmoveNumber);
