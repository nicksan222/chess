//! History-tip inspection, invalid-state resolution, and final-state recording.

use crate::{
    FinalState, HistoryError, HistoryEvent, HistoryEventKind, HistoryStep, InvalidState, MoveError,
};

use super::Game;

impl Game {
    /// Resolves the newest invalid state, preserving strict reverse order.
    pub fn resolve_latest_invalid(&mut self) -> Result<HistoryStep, HistoryError> {
        self.history.resolve_latest_invalid()
    }

    pub(in crate::game) fn record_invalid(&mut self, invalid: InvalidState) -> Option<HistoryStep> {
        if self.latest_event_kind() == Some(HistoryEventKind::Final) {
            return None;
        }
        Some(
            self.history
                .push(HistoryEvent::Invalid(invalid))
                .expect("invalid events may follow active or invalid history"),
        )
    }

    pub(in crate::game) fn append_final(&mut self, final_state: FinalState) -> HistoryStep {
        self.history
            .push(HistoryEvent::Final(final_state))
            .expect("a final event may seal active history")
    }

    pub(super) fn finalize_if_terminal(&mut self) {
        if let Some(final_state) = self.calculated_final_state() {
            self.append_final(final_state);
        }
    }

    pub(in crate::game) fn blocking_move_error(&self) -> Option<MoveError> {
        match self.history.latest().map(HistoryStep::event) {
            Some(HistoryEvent::Invalid(_)) => Some(MoveError::PendingInvalid),
            Some(HistoryEvent::Final(final_state)) => Some(MoveError::GameOver { final_state }),
            Some(HistoryEvent::Move(_)) | None => None,
        }
    }

    pub(super) fn accepts_moves(&self) -> bool {
        matches!(
            self.history.latest().map(HistoryStep::event),
            None | Some(HistoryEvent::Move(_))
        )
    }

    pub(super) fn latest_event_kind(&self) -> Option<HistoryEventKind> {
        self.history.latest().map(|step| step.event().kind())
    }
}
