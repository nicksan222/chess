use sha2::{Digest, Sha256};

use crate::{Color, DrawClaim, DrawReason, GameStatus};

pub(super) fn update_status(digest: &mut Sha256, status: GameStatus) {
    match status {
        GameStatus::InProgress => digest.update([0]),
        GameStatus::DrawClaimAvailable(claims) => digest.update([
            1,
            claims.contains(DrawClaim::ThreefoldRepetition) as u8,
            claims.contains(DrawClaim::FiftyMoveRule) as u8,
        ]),
        GameStatus::Checkmate { winner } => digest.update([2, color_code(winner)]),
        GameStatus::Stalemate => digest.update([3]),
        GameStatus::Draw { reason } => {
            digest.update([4]);
            update_draw_reason(digest, reason);
        }
    }
}

pub(super) fn update_draw_reason(digest: &mut Sha256, reason: DrawReason) {
    match reason {
        DrawReason::Claimed(claim) => digest.update([0, draw_claim_code(claim)]),
        DrawReason::InsufficientMaterial => digest.update([1]),
        DrawReason::FivefoldRepetition => digest.update([2]),
        DrawReason::SeventyFiveMoveRule => digest.update([3]),
    }
}

pub(super) const fn draw_claim_code(claim: DrawClaim) -> u8 {
    match claim {
        DrawClaim::ThreefoldRepetition => 0,
        DrawClaim::FiftyMoveRule => 1,
    }
}

pub(super) const fn color_code(color: Color) -> u8 {
    match color {
        Color::White => 0,
        Color::Black => 1,
    }
}
