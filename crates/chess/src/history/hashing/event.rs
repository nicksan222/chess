//! Canonical hashing of every authoritative event variant.

use crate::{ChessMove, HistoryEvent, HistoryEventKind, InvalidState};

use super::{
    super::{FinalState, HistoryHash, Ply},
    error::{update_move_error, update_sync_error},
    status::{update_draw_claim, update_draw_reason},
    writer::HashWriter,
};

const HASH_DOMAIN: &[u8] = b"chess.game-history.sha256.v1\0";

tag_enum!(
    /// Event category tag, shared with history-error encodings.
    pub(super) EventTag {
        Move,
        Invalid,
        Final,
    }
);

tag_enum!(InvalidTag {
    Move,
    Synchronization,
    DrawClaim,
    PendingInvalid,
});

tag_enum!(FinalTag {
    Checkmate,
    Stalemate,
    Draw,
    DrawAfter,
});

impl From<HistoryEventKind> for EventTag {
    fn from(kind: HistoryEventKind) -> Self {
        match kind {
            HistoryEventKind::Move => Self::Move,
            HistoryEventKind::Invalid => Self::Invalid,
            HistoryEventKind::Final => Self::Final,
        }
    }
}

/// Computes the cumulative hash for one timeline step.
///
/// The hash covers a history domain, the previous tip, the gapless
/// [`Ply`](crate::Ply), and the canonical [`HistoryEvent`](crate::HistoryEvent)
/// encoding. Each [`HistoryStep`](crate::HistoryStep) therefore commits to
/// the anchor and every preceding event, letting
/// [`GameHistory::verify`](crate::GameHistory::verify) detect skipped
/// plies, forked tips, and mutated events.
pub(in crate::history) fn calculate_hash(
    previous: HistoryHash,
    ply: Ply,
    event: HistoryEvent,
) -> HistoryHash {
    let mut writer = HashWriter::new(HASH_DOMAIN);
    writer.hash(&previous).ply(ply);
    update_event(&mut writer, event);
    writer.finish()
}

fn update_event(writer: &mut HashWriter, event: HistoryEvent) {
    writer.tag(EventTag::from(event.kind()));
    match event {
        HistoryEvent::Move(chess_move) => update_move(writer, chess_move),
        HistoryEvent::Invalid(invalid) => update_invalid(writer, invalid),
        HistoryEvent::Final(final_state) => update_final_state(writer, final_state),
    }
}

fn update_move(writer: &mut HashWriter, chess_move: ChessMove) {
    writer
        .square(chess_move.from())
        .square(chess_move.to())
        .byte(chess_move.promotion_code());
}

/// Mixes an invalid state into the cumulative timeline hash.
///
/// The encoding covers move, synchronization, draw-claim, and pending
/// failures, so stacked invalid states resolved newest-first each carry a
/// distinct commitment to the tip that preceded them.
pub(super) fn update_invalid(writer: &mut HashWriter, invalid: InvalidState) {
    match invalid {
        InvalidState::Move(error) => {
            writer.tag(InvalidTag::Move);
            update_move_error(writer, error);
        }
        InvalidState::Synchronization(error) => {
            writer.tag(InvalidTag::Synchronization);
            update_sync_error(writer, error);
        }
        InvalidState::DrawClaim { claim } => {
            writer.tag(InvalidTag::DrawClaim);
            update_draw_claim(writer, claim);
        }
        InvalidState::PendingInvalid => {
            writer.tag(InvalidTag::PendingInvalid);
        }
    }
}

/// Mixes a terminal result into the cumulative timeline hash.
///
/// The encoding covers checkmate, stalemate, draw, and announced-draw
/// outcomes. Since a [`FinalState`](crate::FinalState) seals the
/// [`GameHistory`](crate::GameHistory) tip permanently, its exact terms
/// stay committed to the anchor-to-tip chain.
pub(super) fn update_final_state(writer: &mut HashWriter, final_state: FinalState) {
    match final_state {
        FinalState::Checkmate { winner } => {
            writer.tag(FinalTag::Checkmate).color(winner);
        }
        FinalState::Stalemate => {
            writer.tag(FinalTag::Stalemate);
        }
        FinalState::Draw { reason } => {
            writer.tag(FinalTag::Draw);
            update_draw_reason(writer, reason);
        }
        FinalState::DrawAfter { claim, chess_move } => {
            writer.tag(FinalTag::DrawAfter);
            update_draw_claim(writer, claim);
            update_move(writer, chess_move);
        }
    }
}
