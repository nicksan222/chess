use core::time::Duration;

use tokio::time::Instant;

use super::ButtonAction;
use crate::pins::Level;

#[cfg(test)]
mod tests;

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
