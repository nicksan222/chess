//! History-tip inspection, invalid-state resolution, and final-state recording.

use crate::{
    FinalState, HistoryError, HistoryEvent, HistoryEventKind, HistoryStep, InvalidState, MoveError,
};

use super::Game;

impl Game {
    /// Resolves the newest invalid state, preserving strict reverse order.
    ///
    /// Invalid events block every valid transition: while one is newest,
    /// [`Game::play`] rejects moves with [`MoveError::PendingInvalid`] and
    /// [`Game::legal_moves`](crate::Game::legal_moves) yields nothing.
    /// Resolution pops only the tip, so stacked invalid events must be
    /// cleared newest-first before valid play resumes. The board cache is
    /// untouched because invalid events never mutate piece placement; the
    /// removal is logged on the `chess::game` target.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::NothingToResolve`](crate::HistoryError::NothingToResolve)
    /// when history is empty or the newest event is a move or a sealing
    /// final event, neither of which may be removed through this API.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Game, GameStatus, Square};
    ///
    /// let mut game = Game::new();
    /// assert!(game.play(ChessMove::new(Square::E7, Square::E5)).is_err());
    /// assert!(matches!(game.status(), GameStatus::Invalid { .. }));
    /// game.resolve_latest_invalid()?;
    /// assert!(game.history().is_empty());
    /// game.play(ChessMove::new(Square::E2, Square::E4))?;
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
    pub fn resolve_latest_invalid(&mut self) -> Result<HistoryStep, HistoryError> {
        let step = self.history.resolve_latest_invalid()?;
        self.log_invalid_resolved(step);
        Ok(step)
    }

    /// Records an invalid event unless a final event sealed the history.
    ///
    /// The invalid event becomes the new tip of the authoritative
    /// [`GameHistory`](crate::GameHistory) and blocks valid transitions
    /// until [`Game::resolve_latest_invalid`] removes it. Recording is
    /// reported as a warning on the `chess::game` log target. Returns
    /// `None` without touching history when the newest event is final,
    /// since sealed timelines accept no further events.
    pub(crate) fn record_invalid(&mut self, invalid: InvalidState) -> Option<HistoryStep> {
        if self.latest_event_kind() == Some(HistoryEventKind::Final) {
            return None;
        }
        Some(
            self.push_event(HistoryEvent::Invalid(invalid))
                .expect("invalid events may follow active or invalid history"),
        )
    }

    /// Seals the authoritative history with a terminal result.
    ///
    /// The final event becomes the permanent tip: no move, invalid, or
    /// further final event may follow, so [`Game::play`] thereafter fails
    /// with [`MoveError::GameOver`](crate::MoveError::GameOver). Callers
    /// must ensure the result is valid for the position; see
    /// [`Game::accept`](crate::Game::accept) for the validation applied to
    /// peer-supplied final events. Sealing is logged on the `chess::game`
    /// target.
    pub(crate) fn append_final(&mut self, final_state: FinalState) -> HistoryStep {
        self.push_event(HistoryEvent::Final(final_state))
            .expect("a final event may seal active history")
    }

    /// Appends the terminal result when the board cache is terminal.
    ///
    /// Derives checkmate, stalemate, or an automatic draw from the current
    /// board cache and seals the history when one applies. This keeps the
    /// board cache and the authoritative history consistent after
    /// construction, local play, and accepted peer moves.
    pub(super) fn finalize_if_terminal(&mut self) {
        if let Some(final_state) = self.calculated_final_state() {
            self.append_final(final_state);
        }
    }

    /// Pushes a local event onto the authoritative history.
    ///
    /// The [`GameHistory`](crate::GameHistory) enforces structural order:
    /// any event may follow active history, only invalid events may follow
    /// an invalid tip, and nothing may follow a final tip. The accepted
    /// step is logged on the `chess::game` target.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError`](crate::HistoryError) when the event is not
    /// permitted after the current tip, e.g. any event after a sealing
    /// final event.
    pub(in crate::game) fn push_event(
        &mut self,
        event: HistoryEvent,
    ) -> Result<HistoryStep, HistoryError> {
        let step = self.history.push(event)?;
        self.log_history_step(step);
        Ok(step)
    }

    /// Appends a peer event whose hashes and order were already validated.
    ///
    /// Used by [`Game::accept`](crate::Game::accept) after chess-semantic
    /// checks pass. Because validation happened upstream, this cannot fail;
    /// the appended step advances the history tip and is logged on the
    /// `chess::game` target.
    pub(in crate::game) fn append_validated_step(&mut self, step: HistoryStep) {
        self.history.append_validated(step);
        self.log_history_step(step);
    }

    /// Returns the error blocking valid play, if history tip blocks it.
    ///
    /// An invalid tip yields [`MoveError::PendingInvalid`](crate::MoveError::PendingInvalid)
    /// until [`Game::resolve_latest_invalid`] clears it newest-first, and
    /// a final tip yields [`MoveError::GameOver`](crate::MoveError::GameOver).
    /// Active history returns `None`, meaning [`Game::play`] may attempt
    /// the move against the board cache.
    pub(crate) fn blocking_move_error(&self) -> Option<MoveError> {
        match self.history.latest().map(HistoryStep::event) {
            Some(HistoryEvent::Invalid(_)) => Some(MoveError::PendingInvalid),
            Some(HistoryEvent::Final(final_state)) => Some(MoveError::GameOver { final_state }),
            Some(HistoryEvent::Move(_)) | None => None,
        }
    }

    /// Returns whether the history tip accepts valid transitions.
    ///
    /// Only active history — empty or tipped with a move event — accepts
    /// them. An invalid tip blocks play until resolved newest-first, and a
    /// final tip seals the timeline permanently. [`Game::legal_moves`](crate::Game::legal_moves)
    /// uses this gate before reading the board cache.
    pub(super) fn accepts_moves(&self) -> bool {
        matches!(
            self.history.latest().map(HistoryStep::event),
            None | Some(HistoryEvent::Move(_))
        )
    }

    /// Returns the category of the newest history event, if any.
    ///
    /// Used to enforce aggregate invariants: [`Game::play`] and sync
    /// handling branch on whether the tip is active, invalid (blocking),
    /// or final (sealing). Returns `None` for empty history, which counts
    /// as active.
    pub(super) fn latest_event_kind(&self) -> Option<HistoryEventKind> {
        self.history.latest().map(|step| step.event().kind())
    }
}
