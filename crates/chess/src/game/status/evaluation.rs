//! Status evaluation from history and the current board cache.

use crate::{DrawReason, FinalState, Game, HistoryEvent, InvalidState};

use super::GameStatus;

impl Game {
    /// Returns the status represented by authoritative history and the board cache.
    ///
    /// Derivation reads the history tip first: a terminal event maps through
    /// [`FinalState`](crate::FinalState), an invalid event reports
    /// [`GameStatus::Invalid`](crate::GameStatus::Invalid). Otherwise the
    /// board cache decides checkmate and stalemate (no legal moves, split by
    /// [`Board::is_in_check`](crate::Board::is_in_check)), then automatic
    /// draws, then claimable draws. A fresh game reports
    /// [`GameStatus::InProgress`](crate::GameStatus::InProgress).
    ///
    /// # Example
    ///
    /// ```
    /// use chess::{Game, GameStatus};
    ///
    /// let game = Game::new();
    /// assert_eq!(game.status(), GameStatus::InProgress);
    /// ```
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
    ///
    /// Convenience over [`Game::status`]: `true` exactly when the history tip
    /// or board derivation reports
    /// [`GameStatus::Checkmate`](crate::GameStatus::Checkmate) (in check with
    /// no legal moves).
    #[must_use]
    pub fn is_checkmate(&self) -> bool {
        matches!(self.status(), GameStatus::Checkmate { .. })
    }

    /// Returns whether the position is stalemate.
    ///
    /// Convenience over [`Game::status`]: `true` exactly when the side to
    /// move has no legal moves while not in check. Stalemate is terminal and
    /// counts as a draw via [`Game::is_draw`].
    #[must_use]
    pub fn is_stalemate(&self) -> bool {
        matches!(self.status(), GameStatus::Stalemate)
    }

    /// Returns whether the game has ended in any kind of draw.
    ///
    /// Convenience over [`Game::status`]: `true` for
    /// [`GameStatus::Stalemate`](crate::GameStatus::Stalemate) and
    /// [`GameStatus::Draw`](crate::GameStatus::Draw), including claimed,
    /// automatic, and announced-move draws. Claim availability alone does not
    /// count.
    #[must_use]
    pub fn is_draw(&self) -> bool {
        matches!(
            self.status(),
            GameStatus::Stalemate | GameStatus::Draw { .. }
        )
    }

    /// Derives checkmate, stalemate, or an automatic draw from the board.
    ///
    /// Ignores the history tip: when the side to move has no legal moves the
    /// result splits on [`Board::is_in_check`](crate::Board::is_in_check),
    /// otherwise automatic-draw rules (insufficient material, fivefold
    /// repetition, seventy-five-move rule) apply. Claims never surface here;
    /// see [`Game::draw_claims`](crate::Game::draw_claims).
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

    /// Returns whether `final_state` could legally seal history right now.
    ///
    /// Calculated mates, stalemates, and automatic draws must match the board
    /// derivation; claimed draws consult current claims, and announced-move
    /// draws revalidate the move on a scratch board. Guards sync and replay
    /// paths against sealing an unavailable result.
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
    ///
    /// Reads only the history tip: `Some` exactly when the latest event is
    /// [`HistoryEvent::Invalid`](crate::HistoryEvent), in which case
    /// [`Game::status`] reports
    /// [`GameStatus::Invalid`](crate::GameStatus::Invalid) and play stays
    /// blocked until newest-first resolution.
    #[must_use]
    pub fn latest_invalid(&self) -> Option<InvalidState> {
        match self.history().latest().map(|step| step.event()) {
            Some(HistoryEvent::Invalid(state)) => Some(state),
            _ => None,
        }
    }
}
