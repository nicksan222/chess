//! Fifty-move, seventy-five-move, and repetition draw thresholds.

use crate::{ChessMove, DrawClaim, DrawClaims, DrawReason, FinalState, Game, MoveError};

use super::{material, repetition};

const FIFTY_MOVE_PLIES: u32 = 100;
const SEVENTY_FIVE_MOVE_PLIES: u32 = 150;
const THREEFOLD_REPETITIONS: u8 = 3;
const FIVEFOLD_REPETITIONS: u8 = 5;

impl Game {
    /// Collects claimable draws for the current board and history tip.
    ///
    /// Reports [`DrawClaim::ThreefoldRepetition`] once the current exact
    /// position (pieces, side to move, rights, effective en passant) has
    /// occurred three times, and [`DrawClaim::FiftyMoveRule`] once the
    /// halfmove clock reaches 100 plies. These are claims only; automatic
    /// draws are derived separately by [`Game::status`](crate::Game::status).
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

    /// Evaluates claimable draws as if `chess_move` were the announced move.
    ///
    /// Validates the move on a scratch board without touching this game, then
    /// counts the resulting position plus the fifty-move clock. Powers
    /// [`Game::draw_claims_after`] and [`Game::claim_draw_after`].
    ///
    /// # Errors
    ///
    /// Returns [`MoveError`] when the announced move is illegal on the
    /// current board.
    pub(in crate::game) fn draw_claims_after_move(
        &self,
        chess_move: ChessMove,
    ) -> Result<DrawClaims, MoveError> {
        let mut board = *self.board();
        board.make_move(chess_move)?;

        let mut claims = DrawClaims::NONE;
        let repetitions =
            repetition::count(self.initial_board(), self.history(), &board).saturating_add(1);
        if repetitions >= THREEFOLD_REPETITIONS {
            claims = claims.with(DrawClaim::ThreefoldRepetition);
        }
        if board.halfmove_clock().value() >= FIFTY_MOVE_PLIES {
            claims = claims.with(DrawClaim::FiftyMoveRule);
        }
        Ok(claims)
    }

    /// Derives an automatic draw from material and history-independent rules.
    ///
    /// Checks insufficient material first, then fivefold repetition (minimum
    /// sixteen history steps guard the scan), then the seventy-five-move
    /// rule. Unlike claimable draws, the result needs no player claim and is
    /// surfaced through [`Game::status`](crate::Game::status).
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
