//! Hash and immutable step values used by transport and persistence.

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
    ///
    /// The bytes are the cumulative commitment to one [`HistoryEvent`]
    /// and every preceding event back to the anchor. [`crate::GameHistory`]
    /// links each new [`HistoryStep`] to the previous tip through
    /// these bytes.
    #[must_use]
    pub const fn from_bytes(bytes: [u8; Self::BYTE_COUNT]) -> Self {
        Self(bytes)
    }

    /// Returns the transport representation.
    ///
    /// The bytes carry the cumulative commitment used as the next
    /// step's previous hash, chaining the anchor to the tip of the
    /// [`crate::GameHistory`] timeline.
    #[must_use]
    pub const fn to_bytes(self) -> [u8; Self::BYTE_COUNT] {
        self.0
    }

    /// Borrows the transport representation.
    ///
    /// The borrowed bytes are the same anchor-to-tip commitment covered
    /// by hash validation in [`GameHistory::verify`](crate::GameHistory::verify).
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
    ///
    /// The ply must be the next gapless [`Ply`] after the local tip, the
    /// previous hash must equal that tip, and the hash must be the
    /// cumulative commitment to the anchor and every event through this
    /// step. Newest-first resolution later restores the previous hash as
    /// the tip when the event is invalid.
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
    ///
    /// The ply is gapless from [`Ply::FIRST`](crate::Ply): the first
    /// retained step has ply one and each successor increments by one up
    /// to the tip.
    #[must_use]
    pub const fn ply(self) -> Ply {
        self.ply
    }

    /// Returns the authoritative event.
    ///
    /// The event's [`HistoryEventKind`](crate::HistoryEventKind) decides
    /// whether the timeline stays active, stacks another invalid state,
    /// or seals permanently with a final state.
    #[must_use]
    pub const fn event(self) -> HistoryEvent {
        self.event
    }

    /// Returns the commitment that must match before this event is applied.
    ///
    /// For the first step this equals the [`GameHistory`](crate::GameHistory)
    /// anchor; otherwise it equals the predecessor's cumulative hash, so
    /// the timeline forms one unbroken anchor-to-tip chain.
    #[must_use]
    pub const fn previous_hash(self) -> HistoryHash {
        self.previous_hash
    }

    /// Returns the commitment to this event and all preceding events.
    ///
    /// The hash covers the previous tip, the step's [`Ply`](crate::Ply),
    /// and its [`HistoryEvent`](crate::HistoryEvent). It becomes the
    /// [`GameHistory`](crate::GameHistory) tip once appended and the
    /// required previous hash of the next step.
    #[must_use]
    pub const fn hash(self) -> HistoryHash {
        self.hash
    }
}
