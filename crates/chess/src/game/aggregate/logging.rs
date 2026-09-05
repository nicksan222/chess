//! Central formatting for optional game lifecycle diagnostics.

use logger::{debug, info, warn};

use crate::{HistoryEvent, HistoryStep};

use super::Game;

const TARGET: &str = "chess::game";

impl Game {
    /// Reports game creation for optional lifecycle diagnostics.
    ///
    /// Emits a `debug`-level record on the `chess::game` target naming the
    /// side to move. Logging requires a `logger` subscriber; without one
    /// this is a no-op and never affects the board cache or history.
    pub(super) fn log_created(&self) {
        debug!(
            target: TARGET,
            "created game; {:?} moves first",
            self.board.side_to_move()
        );
    }

    /// Reports an appended history step for optional diagnostics.
    ///
    /// Move and final events log at `info` level and invalid events at
    /// `warn` level on the `chess::game` target, each with its ply. Called
    /// for every local push and every accepted peer step, so the log
    /// mirrors the authoritative [`GameHistory`](crate::GameHistory). A
    /// no-op without a `logger` subscriber.
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

    /// Reports newest-first resolution of an invalid state.
    ///
    /// Emits an `info`-level record on the `chess::game` target with the
    /// resolved ply and event. Called by [`Game::resolve_latest_invalid`]
    /// after the tip is popped; a no-op without a `logger` subscriber and
    /// never a substitute for inspecting the history itself.
    pub(super) fn log_invalid_resolved(&self, step: HistoryStep) {
        info!(
            target: TARGET,
            "resolved invalid state at ply {}: {:?}",
            step.ply(),
            step.event()
        );
    }
}
