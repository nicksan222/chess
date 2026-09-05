//! Validated event sequence numbers and history counts.

use core::{fmt, num::NonZeroU64};

/// A one-based halfmove index in a game's move history.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct Ply(NonZeroU64);

impl Ply {
    /// The first move in a history.
    pub const FIRST: Self = Self(NonZeroU64::MIN);

    /// Creates a validated one-based ply.
    ///
    /// A [`Ply`] is the gapless one-based position of a
    /// [`HistoryStep`](crate::HistoryStep)
    /// in the [`GameHistory`](crate::GameHistory) timeline, starting at
    /// [`Ply::FIRST`]. [`GameHistory::verify`](crate::GameHistory::verify)
    /// requires each retained step to carry the next consecutive ply.
    ///
    /// # Errors
    ///
    /// Returns [`InvalidPly`] when `value` is zero, since ply numbering
    /// is one-based.
    pub const fn new(value: u64) -> Result<Self, InvalidPly> {
        match NonZeroU64::new(value) {
            Some(value) => Ok(Self(value)),
            None => Err(InvalidPly),
        }
    }

    /// Returns the primitive representation for serialization.
    ///
    /// The value is the one-based index committed to the step's
    /// cumulative [`HistoryHash`](crate::HistoryHash) alongside the
    /// previous tip, so transports can recheck ply sequencing.
    #[must_use]
    pub const fn value(self) -> u64 {
        self.0.get()
    }
}

impl fmt::Display for Ply {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

/// The error returned for ply zero.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct InvalidPly;

impl fmt::Display for InvalidPly {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a ply must be at least one")
    }
}

impl_error!(InvalidPly);

/// The number of events retained by a [`crate::GameHistory`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct HistoryCount(usize);

impl HistoryCount {
    /// No retained events.
    pub const ZERO: Self = Self(0);

    /// Returns the primitive representation for collection boundaries.
    ///
    /// The value counts retained [`HistoryStep`](crate::HistoryStep)
    /// values, so the next ply is `value + 1` and
    /// [`GameHistory::verify`](crate::GameHistory::verify) replays exactly
    /// this many links from the anchor to the tip.
    #[must_use]
    pub const fn value(self) -> usize {
        self.0
    }

    /// Builds a count from the number of retained timeline steps.
    ///
    /// The count tracks how many [`HistoryStep`](crate::HistoryStep)
    /// values sit between the anchor and the tip, so the next ply is
    /// `count + 1` and stays gapless from [`Ply::FIRST`].
    pub(super) const fn from_len(value: usize) -> Self {
        Self(value)
    }
}

impl fmt::Display for HistoryCount {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}
