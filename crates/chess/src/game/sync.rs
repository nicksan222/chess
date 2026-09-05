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
    ///
    /// Validation applies in layers: sequence number, previous-hash link,
    /// event hash, structural history transition, move legality against the
    /// board cache, canonical promotion form, and — for final events —
    /// semantic availability for the resulting position. Invalid events
    /// from peers are stored without touching the board cache; accepted
    /// moves update the cache and are logged on the `chess::game` target.
    ///
    /// # Errors
    ///
    /// Returns [`GameSyncError::History`](crate::GameSyncError::History)
    /// when hashes, ordering, transitions, or final-state availability
    /// fail, and [`GameSyncError::Move`](crate::GameSyncError::Move) when
    /// the move is illegal locally or not in canonical promotion form.
    /// Each failure is retained as a synchronization invalid event —
    /// [`InvalidState::Synchronization`](crate::InvalidState) — unless a
    /// final event already sealed history.
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{ChessMove, Game, HistoryEvent, Square};
    ///
    /// let mut first = Game::new();
    /// let step = first.play(ChessMove::new(Square::E2, Square::E4))?;
    /// assert!(matches!(step.event(), HistoryEvent::Move(_)));
    /// let mut second = Game::new();
    /// second.accept(step)?;
    /// assert_eq!(second.board(), first.board());
    /// second.verify()?;
    /// # Ok::<(), Box<dyn core::error::Error>>(())
    /// ```
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

    /// Applies a hash-validated peer move to the board cache.
    ///
    /// Replays the move against the cache, rejects non-canonical
    /// promotions, then stores the validated step and derives any automatic
    /// final event exactly as [`Game::play`] does. Failures are retained as
    /// [`InvalidState::Synchronization`](crate::InvalidState::Synchronization)
    /// events unless history is already sealed.
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
