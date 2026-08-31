use crate::{DrawClaim, DrawClaims, DrawReason, FinalState, Game};

use super::{material, repetition};

const FIFTY_MOVE_PLIES: u32 = 100;
const SEVENTY_FIVE_MOVE_PLIES: u32 = 150;
const THREEFOLD_REPETITIONS: u8 = 3;
const FIVEFOLD_REPETITIONS: u8 = 5;

impl Game {
    pub(in crate::game) fn current_draw_claims(&self) -> DrawClaims {
        let mut claims = DrawClaims::NONE;
        if self.history().len().value() >= 8 && self.position_repetitions() >= THREEFOLD_REPETITIONS
        {
            claims = claims.with(DrawClaim::ThreefoldRepetition);
        }
        if self.board().halfmove_clock().value() >= FIFTY_MOVE_PLIES {
            claims = claims.with(DrawClaim::FiftyMoveRule);
        }
        claims
    }

    pub(in crate::game) fn automatic_draw(&self) -> Option<FinalState> {
        if material::is_insufficient(self.board()) {
            return Some(FinalState::Draw {
                reason: DrawReason::InsufficientMaterial,
            });
        }
        if self.history().len().value() >= 16 && self.position_repetitions() >= FIVEFOLD_REPETITIONS
        {
            return Some(FinalState::Draw {
                reason: DrawReason::FivefoldRepetition,
            });
        }
        (self.board().halfmove_clock().value() >= SEVENTY_FIVE_MOVE_PLIES).then_some(
            FinalState::Draw {
                reason: DrawReason::SeventyFiveMoveRule,
            },
        )
    }

    fn position_repetitions(&self) -> u8 {
        repetition::count(self.initial_board(), self.history(), self.board())
    }
}
