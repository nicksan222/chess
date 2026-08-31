use sha2::{Digest, Sha256};

use crate::{GameSyncError, MoveError};

use super::{
    super::HistoryError,
    status::{color_code, update_status},
};

pub(super) fn update_move_error(digest: &mut Sha256, error: MoveError) {
    match error {
        MoveError::GameOver { status } => {
            digest.update([0]);
            update_status(digest, status);
        }
        MoveError::NoPiece { square } => digest.update([1, square.index().value()]),
        MoveError::WrongSide { expected, actual } => {
            digest.update([2, color_code(expected), color_code(actual)]);
        }
        MoveError::IllegalDestination { from, to } => {
            digest.update([3, from.index().value(), to.index().value()]);
        }
        MoveError::UnexpectedPromotion => digest.update([4]),
        MoveError::InvalidPromotion => digest.update([5]),
        MoveError::NonCanonicalPromotion => digest.update([6]),
        MoveError::StalePiece => digest.update([7]),
    }
}

pub(super) fn update_sync_error(digest: &mut Sha256, error: GameSyncError) {
    match error {
        GameSyncError::History(error) => {
            digest.update([0]);
            update_history_error(digest, error);
        }
        GameSyncError::Move(error) => {
            digest.update([1]);
            update_move_error(digest, error);
        }
    }
}

fn update_history_error(digest: &mut Sha256, error: HistoryError) {
    match error {
        HistoryError::Ply { expected, actual } => {
            digest.update([0]);
            digest.update(expected.value().to_be_bytes());
            digest.update(actual.value().to_be_bytes());
        }
        HistoryError::PreviousHash {
            ply,
            expected,
            actual,
        } => {
            digest.update([1]);
            digest.update(ply.value().to_be_bytes());
            digest.update(expected.as_bytes());
            digest.update(actual.as_bytes());
        }
        HistoryError::Hash {
            ply,
            expected,
            actual,
        } => {
            digest.update([2]);
            digest.update(ply.value().to_be_bytes());
            digest.update(expected.as_bytes());
            digest.update(actual.as_bytes());
        }
        HistoryError::Tip { expected, actual } => {
            digest.update([3]);
            digest.update(expected.as_bytes());
            digest.update(actual.as_bytes());
        }
    }
}
