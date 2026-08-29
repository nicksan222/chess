use core::{fmt, num::NonZeroU64};

/// A one-based halfmove index in a game's move history.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct Ply(NonZeroU64);

impl Ply {
    /// The first move in a history.
    pub const FIRST: Self = Self(NonZeroU64::MIN);

    /// Creates a validated one-based ply.
    pub const fn new(value: u64) -> Result<Self, InvalidPly> {
        match NonZeroU64::new(value) {
            Some(value) => Ok(Self(value)),
            None => Err(InvalidPly),
        }
    }

    /// Returns the primitive representation for serialization.
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

impl core::error::Error for InvalidPly {}

/// The number of moves retained by a [`crate::MoveHistory`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct MoveCount(usize);

impl MoveCount {
    /// No retained moves.
    pub const ZERO: Self = Self(0);

    /// Returns the primitive representation for collection boundaries.
    #[must_use]
    pub const fn value(self) -> usize {
        self.0
    }

    pub(super) const fn from_len(value: usize) -> Self {
        Self(value)
    }
}

impl fmt::Display for MoveCount {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}
