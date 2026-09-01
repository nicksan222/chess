//! Claimable draw inspection and claim finalization.

use core::fmt;

use crate::{
    ChessMove, DrawClaim, DrawClaims, DrawReason, FinalState, Game, HistoryEvent, InvalidState,
    MoveError,
};

/// A draw could not be claimed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DrawClaimError {
    /// The requested claim is not available.
    Unavailable {
        /// The unavailable claim.
        claim: DrawClaim,
    },
    /// The move announced with the claim is not legal.
    Move(MoveError),
}

impl fmt::Display for DrawClaimError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Unavailable { claim } => {
                write!(formatter, "the {claim} draw is not available")
            }
            Self::Move(error) => write!(formatter, "the announced move is not legal: {error}"),
        }
    }
}

impl core::error::Error for DrawClaimError {
    fn source(&self) -> Option<&(dyn core::error::Error + 'static)> {
        match self {
            Self::Unavailable { .. } => None,
            Self::Move(error) => Some(error),
        }
    }
}

impl Game {
    /// Returns the draws the side to move may claim in the current position.
    #[must_use]
    pub fn draw_claims(&self) -> DrawClaims {
        match self.history().latest().map(|step| step.event()) {
            None | Some(HistoryEvent::Move(_)) => self.current_draw_claims(),
            Some(HistoryEvent::Invalid(_) | HistoryEvent::Final(_)) => DrawClaims::NONE,
        }
    }

    /// Claims an available draw and seals authoritative history.
    ///
    /// An unavailable claim is retained as [`InvalidState::DrawClaim`] and
    /// blocks further play until it is resolved. A successful claim appends a
    /// [`FinalState::Draw`] and can never be undone.
    pub fn claim_draw(&mut self, claim: DrawClaim) -> Result<(), DrawClaimError> {
        if !self.draw_claims().contains(claim) {
            self.record_invalid(InvalidState::DrawClaim { claim });
            return Err(DrawClaimError::Unavailable { claim });
        }
        self.append_final(FinalState::Draw {
            reason: DrawReason::Claimed(claim),
        });
        Ok(())
    }

    /// Claims a draw by announcing a legal move that would make it available.
    ///
    /// The announced move is retained as evidence for the claim but is not
    /// applied to the board.
    pub fn claim_draw_after(
        &mut self,
        chess_move: ChessMove,
        claim: DrawClaim,
    ) -> Result<(), DrawClaimError> {
        let available = match self.draw_claims_after(chess_move) {
            Ok(available) => available,
            Err(error) => {
                self.record_invalid(InvalidState::DrawClaim { claim });
                return Err(DrawClaimError::Move(error));
            }
        };
        if !available.contains(claim) {
            self.record_invalid(InvalidState::DrawClaim { claim });
            return Err(DrawClaimError::Unavailable { claim });
        }
        self.append_final(FinalState::DrawAfter { claim, chess_move });
        Ok(())
    }

    /// Returns draws made claimable by `chess_move` without changing this game.
    ///
    /// The move is validated and evaluated as the player's announced move, but
    /// neither the board nor authoritative history is changed.
    pub fn draw_claims_after(&self, chess_move: ChessMove) -> Result<DrawClaims, MoveError> {
        if let Some(error) = self.blocking_move_error() {
            return Err(error);
        }
        self.draw_claims_after_move(chess_move)
    }
}
