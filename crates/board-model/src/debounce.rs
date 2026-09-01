//! Turning noisy sensor reads into settled changes.
//!
//! Hall outputs can briefly change near a magnet's operate/release threshold.
//! Requiring consecutive samples also rejects I2C glitches without adding RC
//! delay to any of the 64 active-low sense lines.
//!
//! The rule is simple and stateful: a square has to read the same way for a
//! number of consecutive samples before the change is believed. Chess moves take
//! hundreds of milliseconds, leaving ample latency margin for this filtering.

use chess::Square;

use crate::occupancy::Occupancy;

/// A settled change on one square.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SquareChange {
    /// The square that changed.
    pub square: Square,
    /// Whether the square now holds a piece.
    pub occupied: bool,
}

/// Filters bounce out of a stream of raw board readings.
///
/// Construct it with the number of consecutive agreeing samples a change needs.
/// A count of one accepts every reading, which is only useful in tests.
#[derive(Clone, Debug)]
pub struct Debouncer {
    settled: Occupancy,
    candidate: Occupancy,
    agreements: u8,
    required: u8,
}

impl Debouncer {
    /// Creates a debouncer that starts from an empty board.
    ///
    /// `required` is clamped to at least one, because zero agreeing samples
    /// would mean accepting a change nothing had reported.
    #[must_use]
    pub const fn new(required: u8) -> Self {
        Self {
            settled: Occupancy::EMPTY,
            candidate: Occupancy::EMPTY,
            agreements: 0,
            required: if required == 0 { 1 } else { required },
        }
    }

    /// Creates a debouncer that starts from a known board state.
    ///
    /// Use this when the host has just read the board and wants the first
    /// sample after startup to produce no changes rather than 32 of them.
    #[must_use]
    pub const fn starting_from(settled: Occupancy, required: u8) -> Self {
        Self {
            settled,
            candidate: settled,
            agreements: 0,
            required: if required == 0 { 1 } else { required },
        }
    }

    /// The board state as currently believed.
    #[must_use]
    pub const fn settled(&self) -> Occupancy {
        self.settled
    }

    /// How many consecutive agreeing samples a change needs.
    #[must_use]
    pub const fn required(&self) -> u8 {
        self.required
    }

    /// Offers a fresh reading, returning the bitmap of squares that settled.
    ///
    /// A reading that disagrees with the pending candidate restarts the count
    /// rather than accumulating, so a contact chattering between states never
    /// crosses the threshold.
    pub fn observe(&mut self, reading: Occupancy) -> u64 {
        if reading != self.candidate {
            self.candidate = reading;
            self.agreements = 1;
        } else {
            self.agreements = self.agreements.saturating_add(1);
        }

        if self.agreements < self.required || self.candidate == self.settled {
            return 0;
        }

        let changed = self.settled.difference(self.candidate);
        self.settled = self.candidate;
        changed
    }

    /// Offers a fresh reading and iterates the changes it settled.
    ///
    /// The returned iterator borrows nothing, so the debouncer can be offered
    /// another reading while an earlier iterator is still in scope.
    pub fn changes(&mut self, reading: Occupancy) -> impl Iterator<Item = SquareChange> + use<> {
        let changed = self.observe(reading);
        let settled = self.settled;
        Square::all().filter_map(move |square| {
            let bit = 1_u64 << square.index().value();
            (changed & bit != 0).then_some(SquareChange {
                square,
                occupied: settled.contains(square),
            })
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chess::Square;

    fn one(square: Square) -> Occupancy {
        Occupancy::EMPTY.with(square, true)
    }

    #[test]
    fn a_change_is_not_believed_until_it_repeats() {
        let mut debouncer = Debouncer::new(3);
        assert_eq!(debouncer.observe(one(Square::E2)), 0);
        assert_eq!(debouncer.observe(one(Square::E2)), 0);
        let changed = debouncer.observe(one(Square::E2));
        assert_eq!(changed.count_ones(), 1);
        assert!(debouncer.settled().contains(Square::E2));
    }

    #[test]
    fn chatter_never_settles() {
        let mut debouncer = Debouncer::new(3);
        for _ in 0..20 {
            assert_eq!(debouncer.observe(one(Square::E2)), 0);
            assert_eq!(debouncer.observe(Occupancy::EMPTY), 0);
        }
        assert_eq!(debouncer.settled(), Occupancy::EMPTY);
    }

    #[test]
    fn a_settled_reading_repeated_reports_nothing_further() {
        let mut debouncer = Debouncer::new(2);
        debouncer.observe(one(Square::A1));
        assert_eq!(debouncer.observe(one(Square::A1)).count_ones(), 1);
        for _ in 0..5 {
            assert_eq!(debouncer.observe(one(Square::A1)), 0);
        }
    }

    #[test]
    fn starting_from_a_known_board_reports_no_initial_changes() {
        let start = one(Square::D4);
        let mut debouncer = Debouncer::starting_from(start, 1);
        assert_eq!(debouncer.observe(start), 0);
        assert_eq!(debouncer.settled(), start);
    }

    #[test]
    fn a_required_count_of_zero_is_treated_as_one() {
        let mut debouncer = Debouncer::new(0);
        assert_eq!(debouncer.required(), 1);
        assert_eq!(debouncer.observe(one(Square::B2)).count_ones(), 1);
    }

    #[test]
    fn changes_name_the_square_and_its_new_state() {
        let mut debouncer = Debouncer::new(1);
        let mut changes = debouncer.changes(one(Square::G7));
        assert_eq!(
            changes.next(),
            Some(SquareChange {
                square: Square::G7,
                occupied: true,
            })
        );
        assert_eq!(changes.next(), None);

        let mut lifted = debouncer.changes(Occupancy::EMPTY);
        assert_eq!(
            lifted.next(),
            Some(SquareChange {
                square: Square::G7,
                occupied: false,
            })
        );
        assert_eq!(lifted.next(), None);
    }

    #[test]
    fn a_move_settles_as_two_changes() {
        let mut debouncer = Debouncer::starting_from(one(Square::E2), 1);
        let mut changes = debouncer.changes(one(Square::E4));
        let first = changes.next().expect("lift");
        let second = changes.next().expect("place");
        assert_eq!(changes.next(), None);
        assert_eq!(
            (first.square, first.occupied),
            (Square::E2, false),
            "the piece leaves e2"
        );
        assert_eq!(
            (second.square, second.occupied),
            (Square::E4, true),
            "and lands on e4"
        );
    }
}
