use sha2::{Digest, Sha256};

use crate::{ChessMove, HistoryEvent, InvalidState};

use super::{
    super::{FinalState, HistoryHash, Ply},
    error::{update_move_error, update_sync_error},
    status::{color_code, draw_claim_code, update_draw_reason},
};

const HASH_DOMAIN: &[u8] = b"chess.game-history.sha256.v1\0";

pub(in crate::game::history) fn calculate_hash(
    previous: HistoryHash,
    ply: Ply,
    event: HistoryEvent,
) -> HistoryHash {
    let mut digest = Sha256::new();
    digest.update(HASH_DOMAIN);
    digest.update(previous.as_bytes());
    digest.update(ply.value().to_be_bytes());
    update_event(&mut digest, event);
    HistoryHash::from_bytes(digest.finalize().into())
}

fn update_event(digest: &mut Sha256, event: HistoryEvent) {
    match event {
        HistoryEvent::Move(chess_move) => {
            digest.update([0]);
            update_move(digest, chess_move);
        }
        HistoryEvent::Invalid(invalid) => {
            digest.update([1]);
            update_invalid(digest, invalid);
        }
        HistoryEvent::Final(final_state) => {
            digest.update([2]);
            update_final(digest, final_state);
        }
    }
}

fn update_move(digest: &mut Sha256, chess_move: ChessMove) {
    digest.update([
        chess_move.from().index().value(),
        chess_move.to().index().value(),
        chess_move.promotion_code(),
    ]);
}

fn update_invalid(digest: &mut Sha256, invalid: InvalidState) {
    match invalid {
        InvalidState::Move(error) => {
            digest.update([0]);
            update_move_error(digest, error);
        }
        InvalidState::Synchronization(error) => {
            digest.update([1]);
            update_sync_error(digest, error);
        }
        InvalidState::DrawClaim { claim } => digest.update([2, draw_claim_code(claim)]),
        InvalidState::PendingInvalid => digest.update([3]),
    }
}

fn update_final(digest: &mut Sha256, final_state: FinalState) {
    match final_state {
        FinalState::Checkmate { winner } => digest.update([0, color_code(winner)]),
        FinalState::Stalemate => digest.update([1]),
        FinalState::Draw { reason } => {
            digest.update([2]);
            update_draw_reason(digest, reason);
        }
    }
}
