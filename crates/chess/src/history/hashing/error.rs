//! Canonical hashing of invalid-operation details.

use crate::{GameSyncError, HistoryEventKind, MoveError};

use super::{
    super::HistoryError,
    event::{EventTag, update_final_state},
    writer::HashWriter,
};

tag_enum!(MoveErrorTag {
    GameOver,
    PendingInvalid,
    NoPiece,
    WrongSide,
    IllegalDestination,
    UnexpectedPromotion,
    InvalidPromotion,
    NonCanonicalPromotion,
    StalePiece,
});

tag_enum!(SyncErrorTag { History, Move });

tag_enum!(HistoryErrorTag {
    Ply,
    PreviousHash,
    Hash,
    InvalidTransition,
    NothingToResolve,
    Tip,
});

/// Mixes a movefailure into the cumulative timeline hash.
///
/// The encoding covers every [`MoveError`](crate::MoveError) variant, so
/// distinct invalid-move details produce distinct [`crate::HistoryStep`]
/// commitments anchored to the previous tip.
pub(super) fn update_move_error(writer: &mut HashWriter, error: MoveError) {
    match error {
        MoveError::GameOver { final_state } => {
            writer.tag(MoveErrorTag::GameOver);
            update_final_state(writer, final_state);
        }
        MoveError::PendingInvalid => {
            writer.tag(MoveErrorTag::PendingInvalid);
        }
        MoveError::NoPiece { square } => {
            writer.tag(MoveErrorTag::NoPiece).square(square);
        }
        MoveError::WrongSide { expected, actual } => {
            writer
                .tag(MoveErrorTag::WrongSide)
                .color(expected)
                .color(actual);
        }
        MoveError::IllegalDestination { from, to } => {
            writer
                .tag(MoveErrorTag::IllegalDestination)
                .square(from)
                .square(to);
        }
        MoveError::UnexpectedPromotion => {
            writer.tag(MoveErrorTag::UnexpectedPromotion);
        }
        MoveError::InvalidPromotion => {
            writer.tag(MoveErrorTag::InvalidPromotion);
        }
        MoveError::NonCanonicalPromotion => {
            writer.tag(MoveErrorTag::NonCanonicalPromotion);
        }
        MoveError::StalePiece => {
            writer.tag(MoveErrorTag::StalePiece);
        }
    }
}

/// Mixes a synchronization failure into the cumulative timeline hash.
///
/// The encoding covers nested history and move failures, so a retained
/// [`InvalidState::Synchronization`](crate::InvalidState) step commits to
/// the exact mismatch that blocked peer synchronization.
pub(super) fn update_sync_error(writer: &mut HashWriter, error: GameSyncError) {
    match error {
        GameSyncError::History(error) => {
            writer.tag(SyncErrorTag::History);
            update_history_error(writer, error);
        }
        GameSyncError::Move(error) => {
            writer.tag(SyncErrorTag::Move);
            update_move_error(writer, error);
        }
    }
}

fn update_history_error(writer: &mut HashWriter, error: HistoryError) {
    match error {
        HistoryError::Ply { expected, actual } => {
            writer.tag(HistoryErrorTag::Ply).ply(expected).ply(actual);
        }
        HistoryError::PreviousHash {
            ply,
            expected,
            actual,
        } => {
            writer
                .tag(HistoryErrorTag::PreviousHash)
                .ply(ply)
                .hash(&expected)
                .hash(&actual);
        }
        HistoryError::Hash {
            ply,
            expected,
            actual,
        } => {
            writer
                .tag(HistoryErrorTag::Hash)
                .ply(ply)
                .hash(&expected)
                .hash(&actual);
        }
        HistoryError::InvalidTransition { current, incoming } => {
            writer.tag(HistoryErrorTag::InvalidTransition);
            update_optional_event_kind(writer, current);
            writer.tag(EventTag::from(incoming));
        }
        HistoryError::NothingToResolve { current } => {
            writer.tag(HistoryErrorTag::NothingToResolve);
            update_optional_event_kind(writer, current);
        }
        HistoryError::Tip { expected, actual } => {
            writer
                .tag(HistoryErrorTag::Tip)
                .hash(&expected)
                .hash(&actual);
        }
    }
}

/// Writes a presence byte, then the kind tag when present.
fn update_optional_event_kind(writer: &mut HashWriter, kind: Option<HistoryEventKind>) {
    match kind {
        Some(kind) => writer.byte(1).tag(EventTag::from(kind)),
        None => writer.byte(0),
    };
}
