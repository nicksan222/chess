//! Time-based debounce for active-low control-panel buttons.

use core::time::Duration;
use tokio::time::Instant;

use super::{buttons::ButtonAction, pins::Level};

/// Accepts a new level once it has held for `debounce`.
pub(super) struct Debouncer {
    debounce: Duration,
    stable: Level,
    candidate: Option<(Level, Instant)>,
}

impl Debouncer {
    pub(super) fn new(initial: Level, debounce: Duration) -> Self {
        Self {
            debounce,
            stable: initial,
            candidate: None,
        }
    }

    pub(super) fn interrupt(&mut self) {
        self.candidate = None;
    }

    pub(super) fn observe(&mut self, level: Level, observed_at: Instant) -> Option<ButtonAction> {
        if level == self.stable {
            self.candidate = None;
            return None;
        }

        match self.candidate {
            Some((candidate, since)) if candidate == level => {
                if observed_at.duration_since(since) < self.debounce {
                    return None;
                }
            }
            _ => {
                self.candidate = Some((level, observed_at));
                return None;
            }
        }

        self.stable = level;
        self.candidate = None;
        Some(match level {
            Level::Low => ButtonAction::Pressed,
            Level::High => ButtonAction::Released,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tuning::ButtonTuning;

    const POLL_INTERVAL: Duration = ButtonTuning::DEFAULT.poll_interval;
    const DEBOUNCE: Duration = ButtonTuning::DEFAULT.debounce;

    #[test]
    fn bounce_and_held_levels_emit_only_stable_edges() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High, DEBOUNCE);
        assert_eq!(button.observe(Level::Low, start), None);
        assert_eq!(button.observe(Level::High, start + POLL_INTERVAL), None);
        assert_eq!(button.observe(Level::Low, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::Low, start + DEBOUNCE * 2),
            Some(ButtonAction::Pressed)
        );
        assert_eq!(button.observe(Level::Low, start + DEBOUNCE * 3), None);
        assert_eq!(button.observe(Level::High, start + DEBOUNCE * 4), None);
        assert_eq!(
            button.observe(Level::High, start + DEBOUNCE * 5),
            Some(ButtonAction::Released)
        );
    }

    #[test]
    fn transition_waits_for_the_complete_debounce_period() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High, DEBOUNCE);

        assert_eq!(button.observe(Level::Low, start), None);
        assert_eq!(
            button.observe(Level::Low, start + DEBOUNCE - POLL_INTERVAL),
            None
        );
        assert_eq!(
            button.observe(Level::Low, start + DEBOUNCE),
            Some(ButtonAction::Pressed)
        );
    }

    #[test]
    fn returning_to_the_stable_level_cancels_the_candidate() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High, DEBOUNCE);

        assert_eq!(button.observe(Level::Low, start), None);
        assert_eq!(button.observe(Level::High, start + POLL_INTERVAL), None);
        assert_eq!(button.observe(Level::Low, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::Low, start + DEBOUNCE * 2),
            Some(ButtonAction::Pressed)
        );
    }

    #[test]
    fn read_failure_restarts_debounce_without_losing_last_stable_level() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::Low, DEBOUNCE);
        assert_eq!(button.observe(Level::High, start), None);
        button.interrupt();
        assert_eq!(button.observe(Level::High, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::High, start + DEBOUNCE * 2),
            Some(ButtonAction::Released)
        );
    }

    #[test]
    fn opposite_level_replaces_the_candidate_and_restarts_the_window() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::Low, DEBOUNCE);

        // High becomes a candidate, then Low (stable) cancels it; a later High
        // must wait a full period from its own first sighting.
        assert_eq!(button.observe(Level::High, start), None);
        assert_eq!(button.observe(Level::Low, start + DEBOUNCE / 2), None);
        assert_eq!(button.observe(Level::High, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::High, start + DEBOUNCE * 2 - POLL_INTERVAL),
            None
        );
        assert_eq!(
            button.observe(Level::High, start + DEBOUNCE * 2),
            Some(ButtonAction::Released)
        );
    }

    #[test]
    fn press_release_press_chain_needs_a_full_window_for_each_edge() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High, DEBOUNCE);
        let mut edges = Vec::new();
        // One sample per poll for 6 periods at each level.
        let mut now = start;
        for level in [Level::Low, Level::High, Level::Low] {
            for _ in 0..=(DEBOUNCE.as_millis() / POLL_INTERVAL.as_millis()) {
                if let Some(action) = button.observe(level, now) {
                    edges.push(action);
                }
                now += POLL_INTERVAL;
            }
        }
        assert_eq!(
            edges,
            [
                ButtonAction::Pressed,
                ButtonAction::Released,
                ButtonAction::Pressed
            ]
        );
    }

    #[test]
    fn interrupt_without_a_candidate_is_harmless() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High, DEBOUNCE);
        button.interrupt();
        assert_eq!(button.observe(Level::High, start), None);
        assert_eq!(button.observe(Level::Low, start), None);
        assert_eq!(
            button.observe(Level::Low, start + DEBOUNCE),
            Some(ButtonAction::Pressed)
        );
    }

    #[test]
    fn initial_level_is_a_baseline_not_a_synthetic_press() {
        let mut button = Debouncer::new(Level::Low, DEBOUNCE);
        assert_eq!(button.observe(Level::Low, Instant::now()), None);
    }

    #[test]
    fn a_longer_debounce_holds_back_the_edge_until_it_elapses() {
        let start = Instant::now();
        let debounce = Duration::from_millis(50);
        let mut button = Debouncer::new(Level::High, debounce);

        assert_eq!(button.observe(Level::Low, start), None);
        assert_eq!(button.observe(Level::Low, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::Low, start + debounce - POLL_INTERVAL),
            None
        );
        assert_eq!(
            button.observe(Level::Low, start + debounce),
            Some(ButtonAction::Pressed)
        );
    }
}
