use core::fmt;

use super::{HistoryEventKind, MoveHash, Ply};

/// The reason a move-history link failed validation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HistoryError {
    /// The incoming step is not next in sequence.
    Ply {
        /// The required ply.
        expected: Ply,
        /// The received ply.
        actual: Ply,
    },
    /// The incoming step does not commit to the local history tip.
    PreviousHash {
        /// The incoming step's ply.
        ply: Ply,
        /// The local tip.
        expected: MoveHash,
        /// The received previous hash.
        actual: MoveHash,
    },
    /// The step's cumulative hash is incorrect.
    Hash {
        /// The invalid step's ply.
        ply: Ply,
        /// The recomputed hash.
        expected: MoveHash,
        /// The stored or received hash.
        actual: MoveHash,
    },
    /// The event is not permitted after the current history tip.
    InvalidTransition {
        /// The current event category, if history is nonempty.
        current: Option<HistoryEventKind>,
        /// The event category that was rejected.
        incoming: HistoryEventKind,
    },
    /// No invalid state is available to resolve.
    NothingToResolve {
        /// The current event category, if history is nonempty.
        current: Option<HistoryEventKind>,
    },
    /// The cached tip does not match the final element.
    Tip {
        /// The final element's hash.
        expected: MoveHash,
        /// The cached tip.
        actual: MoveHash,
    },
}

impl fmt::Display for HistoryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Ply { expected, actual } => {
                write!(formatter, "expected ply {expected}, received {actual}")
            }
            Self::PreviousHash { ply, .. } => {
                write!(formatter, "move {ply} does not follow the local history")
            }
            Self::Hash { ply, .. } => write!(formatter, "history event {ply} has an invalid hash"),
            Self::InvalidTransition { .. } => {
                formatter.write_str("the event is not permitted after the current history tip")
            }
            Self::NothingToResolve { .. } => {
                formatter.write_str("the latest history event is not an invalid state")
            }
            Self::Tip { .. } => formatter.write_str("the cached game-history tip is invalid"),
        }
    }
}

impl_error!(HistoryError);
