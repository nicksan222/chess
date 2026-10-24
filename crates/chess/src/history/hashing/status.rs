//! Stable hash encodings for draw claims and draw reasons.

use crate::{DrawClaim, DrawReason};

use super::writer::HashWriter;

tag_enum!(DrawReasonTag {
    Claimed,
    InsufficientMaterial,
    FivefoldRepetition,
    SeventyFiveMoveRule,
});

tag_enum!(DrawClaimTag {
    ThreefoldRepetition,
    FiftyMoveRule,
});

/// Mixes a draw reason into the cumulative timeline hash.
///
/// The encoding covers claimed draws and automatic rules, so distinct
/// terminal [`DrawReason`](crate::DrawReason) values seal the
/// [`GameHistory`](crate::GameHistory) tip with distinct commitments.
pub(super) fn update_draw_reason(writer: &mut HashWriter, reason: DrawReason) {
    match reason {
        DrawReason::Claimed(claim) => {
            writer.tag(DrawReasonTag::Claimed);
            update_draw_claim(writer, claim);
        }
        DrawReason::InsufficientMaterial => {
            writer.tag(DrawReasonTag::InsufficientMaterial);
        }
        DrawReason::FivefoldRepetition => {
            writer.tag(DrawReasonTag::FivefoldRepetition);
        }
        DrawReason::SeventyFiveMoveRule => {
            writer.tag(DrawReasonTag::SeventyFiveMoveRule);
        }
    }
}

/// Mixes a draw claim into the cumulative timeline hash.
///
/// The code keeps [`DrawClaim`](crate::DrawClaim) encodings stable inside
/// invalid and terminal event hashes chained from the anchor to the tip.
pub(super) fn update_draw_claim(writer: &mut HashWriter, claim: DrawClaim) {
    writer.tag(match claim {
        DrawClaim::ThreefoldRepetition => DrawClaimTag::ThreefoldRepetition,
        DrawClaim::FiftyMoveRule => DrawClaimTag::FiftyMoveRule,
    });
}
