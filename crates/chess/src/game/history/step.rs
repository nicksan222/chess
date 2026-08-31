use core::fmt;

use super::{HistoryEvent, Ply};

/// A SHA-256 commitment to one event and every event preceding it.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct HistoryHash([u8; Self::BYTE_COUNT]);

impl HistoryHash {
    /// The number of bytes in a history hash.
    pub const BYTE_COUNT: usize = 32;

    /// The anchor for a history that is not tied to an initial board.
    pub const GENESIS: Self = Self([0; Self::BYTE_COUNT]);

    /// Creates a hash from its transport representation.
    #[must_use]
    pub const fn from_bytes(bytes: [u8; Self::BYTE_COUNT]) -> Self {
        Self(bytes)
    }

    /// Returns the transport representation.
    #[must_use]
    pub const fn to_bytes(self) -> [u8; Self::BYTE_COUNT] {
        self.0
    }

    /// Borrows the transport representation.
    #[must_use]
    pub const fn as_bytes(&self) -> &[u8; Self::BYTE_COUNT] {
        &self.0
    }
}

impl Default for HistoryHash {
    fn default() -> Self {
        Self::GENESIS
    }
}

impl fmt::Display for HistoryHash {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        for byte in self.0 {
            write!(formatter, "{byte:02x}")?;
        }
        Ok(())
    }
}

impl fmt::Debug for HistoryHash {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "HistoryHash({self})")
    }
}

/// One immutable event in a hash-linked game history.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct HistoryStep {
    ply: Ply,
    event: HistoryEvent,
    previous_hash: HistoryHash,
    hash: HistoryHash,
}

impl HistoryStep {
    /// Reconstructs a step received from transport or persistence.
    ///
    /// Use [`crate::GameHistory::try_append`] to validate it before accepting it.
    #[must_use]
    pub const fn from_parts(
        ply: Ply,
        event: HistoryEvent,
        previous_hash: HistoryHash,
        hash: HistoryHash,
    ) -> Self {
        Self {
            ply,
            event,
            previous_hash,
            hash,
        }
    }

    /// Returns this step's one-based sequence index.
    #[must_use]
    pub const fn ply(self) -> Ply {
        self.ply
    }

    /// Returns the authoritative event.
    #[must_use]
    pub const fn event(self) -> HistoryEvent {
        self.event
    }

    /// Returns the commitment that must match before this event is applied.
    #[must_use]
    pub const fn previous_hash(self) -> HistoryHash {
        self.previous_hash
    }

    /// Returns the commitment to this event and all preceding events.
    #[must_use]
    pub const fn hash(self) -> HistoryHash {
        self.hash
    }
}
