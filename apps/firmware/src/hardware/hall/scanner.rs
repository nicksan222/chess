//! One complete scan of the eight banks: reads, filters and reports changes.
//! Kept free of timers and buses so it can be stepped directly in tests.

use embedded_hal::i2c::I2c;

use super::{HallBank, filter::Filter, monitor::Monitor};
use crate::{hardware::PieceEvent, tuning::HallTuning};

pub(super) struct Scanner {
    banks: [(Monitor, Filter); HallBank::COUNT],
}

impl Scanner {
    pub(super) fn new(tuning: HallTuning) -> Self {
        Self {
            banks: HallBank::all()
                .map(|bank| (Monitor::new(bank), Filter::new(tuning.stable_scans))),
        }
    }

    /// Scans every bank once, in address order, and returns the confirmed
    /// piece changes. A bank that fails reports nothing: its squares are
    /// unknown, not empty, and it is reconciled on recovery.
    #[cfg(test)]
    fn scan<I: I2c>(&mut self, i2c: &mut I) -> Vec<PieceEvent> {
        self.scan_while(i2c, || true)
    }

    pub(super) fn scan_while<I: I2c>(
        &mut self,
        i2c: &mut I,
        keep_scanning: impl Fn() -> bool,
    ) -> Vec<PieceEvent> {
        let mut events = Vec::new();
        for (monitor, filter) in &mut self.banks {
            if !keep_scanning() {
                break;
            }
            match monitor.read(i2c) {
                Some(occupied) => {
                    if let Some(change) = filter.observe(occupied) {
                        events.extend(change.events(monitor.bank()));
                    }
                }
                None => filter.interrupt(),
            }
        }
        events
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::hall::fake::Expanders;
    use chess::Square;

    const TUNING: HallTuning = HallTuning::DEFAULT;

    /// Scans until the readings have been stable long enough to report.
    fn settle(scanner: &mut Scanner, expanders: &mut Expanders) -> Vec<PieceEvent> {
        (0..TUNING.stable_scans)
            .flat_map(|_| scanner.scan(expanders))
            .collect()
    }

    #[test]
    fn startup_configures_every_bank_then_reports_the_stable_position() {
        let mut expanders = Expanders::new();
        expanders.place(Square::A1);
        expanders.place(Square::H8);
        let mut scanner = Scanner::new(TUNING);

        assert_eq!(scanner.scan(&mut expanders), []);
        let expected: Vec<_> = HallBank::all()
            .map(HallBank::address)
            .into_iter()
            .flat_map(|address| [(address, vec![0x03, 0xFF]), (address, vec![0x02, 0x00])])
            .collect();
        assert_eq!(expanders.settings(), expected);

        assert_eq!(
            scanner.scan(&mut expanders),
            [
                PieceEvent::Placed(Square::A1),
                PieceEvent::Placed(Square::H8)
            ]
        );
        assert_eq!(scanner.scan(&mut expanders), []);
    }

    #[test]
    fn a_reading_seen_in_one_scan_only_is_ignored() {
        let mut expanders = Expanders::new();
        let mut scanner = Scanner::new(TUNING);
        settle(&mut scanner, &mut expanders);

        expanders.place(Square::D3);
        assert_eq!(scanner.scan(&mut expanders), []);
        expanders.remove(Square::D3);
        assert_eq!(settle(&mut scanner, &mut expanders), []);

        expanders.place(Square::D3);
        assert_eq!(
            settle(&mut scanner, &mut expanders),
            [PieceEvent::Placed(Square::D3)]
        );
        expanders.remove(Square::D3);
        assert_eq!(
            settle(&mut scanner, &mut expanders),
            [PieceEvent::Removed(Square::D3)]
        );
    }

    #[test]
    fn a_failed_bank_is_reconciled_with_what_changed_while_it_was_unknown() {
        let mut expanders = Expanders::new();
        expanders.place(Square::E1);
        expanders.place(Square::G1);
        let mut scanner = Scanner::new(TUNING);
        settle(&mut scanner, &mut expanders);

        // The E1–H2 expander drops off the bus; failure is not emptiness.
        expanders.absent[1] = true;
        assert_eq!(settle(&mut scanner, &mut expanders), []);

        // Meanwhile G1 left and F1 arrived; E1 never moved, so it is not
        // reported again.
        expanders.remove(Square::G1);
        expanders.place(Square::F1);
        expanders.absent[1] = false;
        assert_eq!(
            settle(&mut scanner, &mut expanders),
            [
                PieceEvent::Placed(Square::F1),
                PieceEvent::Removed(Square::G1)
            ]
        );
    }
}
