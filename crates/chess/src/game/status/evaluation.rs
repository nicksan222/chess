//! Status evaluation from history and the current board cache.

use crate::{DrawReason, FinalState, Game, HistoryEvent, InvalidState};

use super::GameStatus;

impl Game {
    /// Returns the status represented by authoritative history and the board cache.
    #[must_use]
    pub fn status(&self) -> GameStatus {
        match self.history().latest().map(|step| step.event()) {
            Some(HistoryEvent::Final(final_state)) => return final_state.into(),
            Some(HistoryEvent::Invalid(state)) => return GameStatus::Invalid { state },
            Some(HistoryEvent::Move(_)) | None => {}
        }

        if let Some(final_state) = self.calculated_final_state() {
            return final_state.into();
        }
        let claims = self.current_draw_claims();
        if claims.is_empty() {
            GameStatus::InProgress
        } else {
            GameStatus::DrawClaimAvailable(claims)
        }
    }

    /// Returns whether the side to move is checkmated.
    #[must_use]
    pub fn is_checkmate(&self) -> bool {
        matches!(self.status(), GameStatus::Checkmate { .. })
    }

    /// Returns whether the position is stalemate.
    #[must_use]
    pub fn is_stalemate(&self) -> bool {
        matches!(self.status(), GameStatus::Stalemate)
    }

    /// Returns whether the game has ended in any kind of draw.
    #[must_use]
    pub fn is_draw(&self) -> bool {
        matches!(
            self.status(),
            GameStatus::Stalemate | GameStatus::Draw { .. }
        )
    }

    pub(in crate::game) fn calculated_final_state(&self) -> Option<FinalState> {
        if self.board().legal_moves().next().is_none() {
            return Some(if self.is_in_check() {
                FinalState::Checkmate {
                    winner: self.side_to_move().opposite(),
                }
            } else {
                FinalState::Stalemate
            });
        }
        self.automatic_draw()
    }

    pub(in crate::game) fn final_state_is_available(&self, final_state: FinalState) -> bool {
        if self.calculated_final_state() == Some(final_state) {
            return true;
        }
        match final_state {
            FinalState::Draw {
                reason: DrawReason::Claimed(claim),
            } => self.current_draw_claims().contains(claim),
            FinalState::DrawAfter { claim, chess_move } => self
                .draw_claims_after_move(chess_move)
                .is_ok_and(|claims| claims.contains(claim)),
            FinalState::Checkmate { .. } | FinalState::Stalemate | FinalState::Draw { .. } => false,
        }
    }

    /// Returns the newest unresolved invalid state.
    #[must_use]
    pub fn latest_invalid(&self) -> Option<InvalidState> {
        match self.history().latest().map(|step| step.event()) {
            Some(HistoryEvent::Invalid(state)) => Some(state),
            _ => None,
        }
    }
}
