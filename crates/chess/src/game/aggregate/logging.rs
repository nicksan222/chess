//! Central formatting for optional game lifecycle diagnostics.

use logger::{debug, info, warn};

use crate::{HistoryEvent, HistoryStep};

use super::Game;

const TARGET: &str = "chess::game";

impl Game {
    pub(super) fn log_created(&self) {
        debug!(
            target: TARGET,
            "created game; {:?} moves first",
            self.board.side_to_move()
        );
    }

    pub(super) fn log_history_step(&self, step: HistoryStep) {
        match step.event() {
            HistoryEvent::Move(chess_move) => info!(
                target: TARGET,
                "recorded move {chess_move} at ply {}",
                step.ply()
            ),
            HistoryEvent::Invalid(invalid) => warn!(
                target: TARGET,
                "recorded invalid state at ply {}: {invalid:?}",
                step.ply()
            ),
            HistoryEvent::Final(final_state) => info!(
                target: TARGET,
                "game ended at ply {}: {final_state:?}",
                step.ply()
            ),
        }
    }

    pub(super) fn log_invalid_resolved(&self, step: HistoryStep) {
        info!(
            target: TARGET,
            "resolved invalid state at ply {}: {:?}",
            step.ply(),
            step.event()
        );
    }
}
