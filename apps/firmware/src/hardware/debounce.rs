//! Time-based debounce for active-low control-panel buttons.

use core::time::Duration;
use tokio::time::Instant;

use super::{buttons::ButtonAction, pins::Level};

pub(super) const POLL_INTERVAL: Duration = Duration::from_millis(5);
const DEBOUNCE: Duration = Duration::from_millis(20);

pub(super) struct Debouncer {
    stable: Level,
    candidate: Option<(Level, Instant)>,
}

impl Debouncer {
    pub(super) fn new(initial: Level) -> Self {
        Self {
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
                if observed_at.duration_since(since) < DEBOUNCE {
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

    #[test]
    fn bounce_and_held_levels_emit_only_stable_edges() {
        let start = Instant::now();
        let mut button = Debouncer::new(Level::High);
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
        let mut button = Debouncer::new(Level::High);

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
        let mut button = Debouncer::new(Level::High);

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
        let mut button = Debouncer::new(Level::Low);
        assert_eq!(button.observe(Level::High, start), None);
        button.interrupt();
        assert_eq!(button.observe(Level::High, start + DEBOUNCE), None);
        assert_eq!(
            button.observe(Level::High, start + DEBOUNCE * 2),
            Some(ButtonAction::Released)
        );
    }

    #[test]
    fn initial_level_is_a_baseline_not_a_synthetic_press() {
        let mut button = Debouncer::new(Level::Low);
        assert_eq!(button.observe(Level::Low, Instant::now()), None);
    }
}
