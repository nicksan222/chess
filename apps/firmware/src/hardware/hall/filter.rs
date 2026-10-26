//! Confirms a bank's occupancy before it is reported.

use super::change::Change;

/// Tracks what was last reported for a bank and what its recent reads agree on.
pub(super) struct Filter {
    /// Consecutive reads that must agree before a change is reported.
    stable_scans: u8,
    /// Starts empty, so the first stable reading reports every occupied square.
    reported: u8,
    candidate: u8,
    /// Consecutive reads of `candidate`; zero after an interruption.
    repeats: u8,
}

impl Filter {
    pub(super) const fn new(stable_scans: u8) -> Self {
        Self {
            stable_scans,
            reported: 0,
            candidate: 0,
            repeats: 0,
        }
    }

    /// Feeds one complete read, one bit per occupied channel. Returns the
    /// change once the reading has held for `stable_scans` reads.
    pub(super) fn observe(&mut self, occupied: u8) -> Option<Change> {
        if self.repeats > 0 && occupied == self.candidate {
            self.repeats = self.repeats.saturating_add(1);
        } else {
            self.candidate = occupied;
            self.repeats = 1;
        }
        if self.repeats < self.stable_scans || occupied == self.reported {
            return None;
        }
        let change = Change {
            before: self.reported,
            after: occupied,
        };
        self.reported = occupied;
        Some(change)
    }

    /// A missed read breaks the run: agreement must start again, while what
    /// was reported is kept so recovery reports only real changes.
    pub(super) fn interrupt(&mut self) {
        self.repeats = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const STABLE_SCANS: u8 = 2;

    fn settle(filter: &mut Filter, occupied: u8) -> Option<Change> {
        (0..STABLE_SCANS)
            .filter_map(|_| filter.observe(occupied))
            .last()
    }

    #[test]
    fn a_reading_is_reported_once_it_has_held() {
        let mut filter = Filter::new(STABLE_SCANS);
        assert_eq!(filter.observe(0b0101), None);
        assert_eq!(
            filter.observe(0b0101),
            Some(Change {
                before: 0,
                after: 0b0101
            })
        );
        assert_eq!(filter.observe(0b0101), None);
    }

    #[test]
    fn a_glitch_restarts_agreement_and_reports_nothing() {
        let mut filter = Filter::new(STABLE_SCANS);
        settle(&mut filter, 0b1000);
        assert_eq!(filter.observe(0b1001), None);
        assert_eq!(settle(&mut filter, 0b1000), None);
    }

    #[test]
    fn an_interruption_restarts_agreement_but_keeps_the_report() {
        let mut filter = Filter::new(STABLE_SCANS);
        settle(&mut filter, 0b0011);
        filter.observe(0b0110);
        filter.interrupt();
        assert_eq!(filter.observe(0b0110), None);
        assert_eq!(
            filter.observe(0b0110),
            Some(Change {
                before: 0b0011,
                after: 0b0110
            })
        );
    }
}
