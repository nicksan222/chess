//! Stable hash encodings for colors, draw claims, and draw reasons.

use sha2::{Digest, Sha256};

use crate::{Color, DrawClaim, DrawReason};

/// Mixes a draw reason into the cumulative timeline hash.
///
/// The encoding covers claimed draws and automatic rules, so distinct
/// terminal [`DrawReason`](crate::DrawReason) values seal the
/// [`GameHistory`](crate::GameHistory) tip with distinct commitments.
pub(super) fn update_draw_reason(digest: &mut Sha256, reason: DrawReason) {
    match reason {
        DrawReason::Claimed(claim) => digest.update([0, draw_claim_code(claim)]),
        DrawReason::InsufficientMaterial => digest.update([1]),
        DrawReason::FivefoldRepetition => digest.update([2]),
        DrawReason::SeventyFiveMoveRule => digest.update([3]),
    }
}

/// Returns the stable hash code for a draw claim.
///
/// The code keeps [`DrawClaim`](crate::DrawClaim) encodings stable inside
/// invalid and terminal event hashes chained from the anchor to the tip.
pub(super) const fn draw_claim_code(claim: DrawClaim) -> u8 {
    match claim {
        DrawClaim::ThreefoldRepetition => 0,
        DrawClaim::FiftyMoveRule => 1,
    }
}

/// Returns the stable hash code for a color.
///
/// The code keeps mover, winner, and piece-color encodings stable inside
/// board anchors and cumulative event hashes.
pub(super) const fn color_code(color: Color) -> u8 {
    match color {
        Color::White => 0,
        Color::Black => 1,
    }
}
