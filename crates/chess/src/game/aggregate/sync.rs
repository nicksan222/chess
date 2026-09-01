//! Validation and application of authoritative events received from peers.

use crate::{
    GameSyncError, HistoryError, HistoryEvent, HistoryEventKind, HistoryStep, InvalidState,
    MoveError,
};

use super::Game;

impl Game {
    /// Verifies and accepts an authoritative history step from a peer.
    ///
    /// Validation covers the sequence number, previous hash, event hash,
    /// structural history transition, move legality, canonical promotion, and
    /// semantic validity of final events. An accepted move updates the board
    /// cache and derives any automatic final event exactly as local play does.
    ///
    /// A synchronization failure is itself retained as an invalid event unless
    /// history is already sealed by a final event. This intentionally makes
    /// divergence visible and blocks further valid transitions until resolved.
    pub fn accept(&mut self, step: HistoryStep) -> Result<(), GameSyncError> {
        if let Err(error) = self.history.validate_next(step) {
            let sync = GameSyncError::History(error);
            self.record_invalid(InvalidState::Synchronization(sync));
            return Err(sync);
        }

        match step.event() {
            HistoryEvent::Move(chess_move) => self.accept_move(step, chess_move),
            HistoryEvent::Invalid(_) => {
                self.append_validated_step(step);
                Ok(())
            }
            HistoryEvent::Final(final_state) => {
                if !self.final_state_is_available(final_state) {
                    let error = HistoryError::InvalidTransition {
                        current: self.latest_event_kind(),
                        incoming: HistoryEventKind::Final,
                    };
                    let sync = GameSyncError::History(error);
                    self.record_invalid(InvalidState::Synchronization(sync));
                    return Err(sync);
                }
                self.append_validated_step(step);
                Ok(())
            }
        }
    }

    fn accept_move(
        &mut self,
        step: HistoryStep,
        chess_move: crate::ChessMove,
    ) -> Result<(), GameSyncError> {
        let mut next = self.board;
        let canonical = match next.make_move(chess_move) {
            Ok(canonical) => canonical,
            Err(error) => {
                let sync = GameSyncError::Move(error);
                self.record_invalid(InvalidState::Synchronization(sync));
                return Err(sync);
            }
        };
        if canonical != chess_move {
            let sync = GameSyncError::Move(MoveError::NonCanonicalPromotion);
            self.record_invalid(InvalidState::Synchronization(sync));
            return Err(sync);
        }
        self.board = next;
        self.append_validated_step(step);
        self.finalize_if_terminal();
        Ok(())
    }
}
