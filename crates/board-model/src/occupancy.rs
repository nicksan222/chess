//! Which squares currently hold a piece.
//!
//! One bit per square, indexed the same way `chess::Square` indexes itself, so
//! a reading from the board and a position from the chess domain line up without
//! a translation step.

use chess::Square;

use crate::mapping::{EXPANDER_COUNT, expander_pin};

/// A snapshot of the board's magnetic sensors.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash)]
pub struct Occupancy(u64);

impl Occupancy {
    /// An empty board.
    pub const EMPTY: Self = Self(0);

    /// Builds a snapshot from a raw bitmap, one bit per square index.
    #[must_use]
    pub const fn from_bits(bits: u64) -> Self {
        Self(bits)
    }

    /// Returns the snapshot as a raw bitmap.
    #[must_use]
    pub const fn bits(self) -> u64 {
        self.0
    }

    /// Whether a square holds a piece.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        self.0 & Self::mask(square) != 0
    }

    /// Returns the snapshot with a square set or cleared.
    #[must_use]
    pub const fn with(self, square: Square, occupied: bool) -> Self {
        if occupied {
            Self(self.0 | Self::mask(square))
        } else {
            Self(self.0 & !Self::mask(square))
        }
    }

    /// How many squares hold a piece.
    #[must_use]
    pub const fn count(self) -> u32 {
        self.0.count_ones()
    }

    /// The squares that differ between two snapshots.
    #[must_use]
    pub const fn difference(self, other: Self) -> u64 {
        self.0 ^ other.0
    }

    /// Iterates the squares that hold a piece, in board index order.
    pub fn squares(self) -> impl Iterator<Item = Square> {
        Square::all().filter(move |square| self.contains(*square))
    }

    /// Builds a snapshot from what the expanders reported.
    ///
    /// `ports` holds two bytes per expander, port A then port B, in device
    /// order. A Hall sensor pulls its active-low output low when a piece is present, so a clear
    /// bit means occupied; this is where that inversion is handled, once.
    #[must_use]
    pub fn from_expander_ports(ports: [u8; (EXPANDER_COUNT * 2) as usize]) -> Self {
        let mut bits = 0_u64;
        for square in Square::all() {
            let pin = expander_pin(square);
            let port = usize::from(pin.device()) * 2 + usize::from(pin.is_port_b());
            let grounded = ports[port] & (1 << pin.bit()) == 0;
            if grounded {
                bits |= Self::mask(square);
            }
        }
        Self(bits)
    }

    const fn mask(square: Square) -> u64 {
        1_u64 << square.index().value()
    }
}

impl From<Occupancy> for u64 {
    fn from(value: Occupancy) -> Self {
        value.bits()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::SQUARE_COUNT;
    use chess::Square;

    #[test]
    fn an_empty_board_holds_nothing() {
        assert_eq!(Occupancy::EMPTY.count(), 0);
        assert_eq!(Occupancy::default(), Occupancy::EMPTY);
        for square in Square::all() {
            assert!(!Occupancy::EMPTY.contains(square));
        }
    }

    #[test]
    fn setting_and_clearing_a_square_round_trips() {
        let board = Occupancy::EMPTY.with(Square::E4, true);
        assert!(board.contains(Square::E4));
        assert_eq!(board.count(), 1);
        assert!(!board.with(Square::E4, false).contains(Square::E4));
    }

    #[test]
    fn squares_iterates_only_occupied_squares_in_index_order() {
        let board = Occupancy::EMPTY
            .with(Square::H8, true)
            .with(Square::A1, true)
            .with(Square::E4, true);
        let mut found = board.squares();
        assert_eq!(found.next(), Some(Square::A1));
        assert_eq!(found.next(), Some(Square::E4));
        assert_eq!(found.next(), Some(Square::H8));
        assert_eq!(found.next(), None);
    }

    #[test]
    fn difference_reports_only_changed_squares() {
        let before = Occupancy::EMPTY.with(Square::E2, true);
        let after = Occupancy::EMPTY.with(Square::E4, true);
        let changed = before.difference(after);
        assert_eq!(changed.count_ones(), 2);
        assert_ne!(changed & (1 << Square::E2.index().value()), 0);
        assert_ne!(changed & (1 << Square::E4.index().value()), 0);
        assert_eq!(before.difference(before), 0);
    }

    #[test]
    fn a_grounded_pin_means_an_occupied_square() {
        // Every pin high: nothing pulled down, so the board is empty.
        assert_eq!(Occupancy::from_expander_ports([0xFF; 8]), Occupancy::EMPTY);
        // Every pin low: every Hall sensor active.
        assert_eq!(
            Occupancy::from_expander_ports([0x00; 8]).count(),
            SQUARE_COUNT as u32
        );
    }

    #[test]
    fn one_grounded_pin_lands_on_the_square_that_owns_it() {
        for square in Square::all() {
            let pin = expander_pin(square);
            let mut ports = [0xFF_u8; 8];
            let port = usize::from(pin.device()) * 2 + usize::from(pin.is_port_b());
            ports[port] &= !(1 << pin.bit());
            let board = Occupancy::from_expander_ports(ports);
            assert_eq!(board.count(), 1, "{square}");
            assert!(board.contains(square), "{square}");
        }
    }
}
