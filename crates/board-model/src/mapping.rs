//! Where each square is read, and where each square is lit.
//!
//! Both mappings are fixed by the board layout, so they are plain functions
//! rather than configuration. If the schematic changes, these change with it and
//! the tests here are what catch the disagreement.

use chess::Square;

use crate::SQUARE_COUNT;

/// Expanders on the bus, one per 4x4 quadrant of the board.
pub const EXPANDER_COUNT: u8 = 4;
/// General-purpose pins on one expander: two eight-bit ports.
pub const PINS_PER_EXPANDER: u8 = 16;
/// The first expander's I2C address. The rest follow consecutively because the
/// quadrant index is strapped onto the device's own address pins.
pub const EXPANDER_BASE_ADDRESS: u8 = 0x20;

/// Which expander pin reads a square.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ExpanderPin {
    device: u8,
    pin: u8,
}

impl ExpanderPin {
    /// The expander index, counting quadrants from a1.
    #[must_use]
    pub const fn device(self) -> u8 {
        self.device
    }

    /// The pin within that expander, 0 through 15. Port A is 0-7.
    #[must_use]
    pub const fn pin(self) -> u8 {
        self.pin
    }

    /// The device's address on the I2C bus.
    #[must_use]
    pub const fn address(self) -> u8 {
        EXPANDER_BASE_ADDRESS + self.device
    }

    /// Whether this pin is on port B rather than port A.
    ///
    /// A read returns two bytes, one per port, so which port a pin belongs to
    /// decides which byte to look in.
    #[must_use]
    pub const fn is_port_b(self) -> bool {
        self.pin >= 8
    }

    /// The bit position within its own port byte.
    #[must_use]
    pub const fn bit(self) -> u8 {
        self.pin % 8
    }
}

const fn file_of(square: Square) -> u8 {
    square.index().value() % 8
}

const fn rank_of(square: Square) -> u8 {
    square.index().value() / 8
}

/// Returns the expander pin that reads a square.
///
/// Quadrants keep the reed traces short on a 320 mm board: an expander sits at
/// the centre of the sixteen squares it serves. Within a quadrant, port A takes
/// the lower two ranks and port B the upper two.
#[must_use]
pub const fn expander_pin(square: Square) -> ExpanderPin {
    let file = file_of(square);
    let rank = rank_of(square);
    ExpanderPin {
        device: (rank / 4) * 2 + (file / 4),
        pin: (rank % 4) * 4 + (file % 4),
    }
}

/// Returns a square's position in the LED chain, counting from zero.
///
/// The chain snakes by rank from a1: left to right along rank 1, right to left
/// along rank 2, and so on. Serpentine wiring is what keeps the run between
/// consecutive LEDs down to one square pitch everywhere.
#[must_use]
pub const fn led_index(square: Square) -> u8 {
    let file = file_of(square);
    let rank = rank_of(square);
    let along = if rank % 2 == 0 { file } else { 7 - file };
    rank * 8 + along
}

/// Returns the square at a position in the LED chain, if that position exists.
#[must_use]
pub fn square_at_led_index(index: u8) -> Option<Square> {
    if usize::from(index) >= SQUARE_COUNT {
        return None;
    }
    let rank = index / 8;
    let along = index % 8;
    let file = if rank % 2 == 0 { along } else { 7 - along };
    Square::all().find(|square| file_of(*square) == file && rank_of(*square) == rank)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chess::Square;

    #[test]
    fn every_square_owns_a_distinct_expander_pin() {
        let mut seen = [false; 64];
        for square in Square::all() {
            let pin = expander_pin(square);
            let slot = usize::from(pin.device()) * 16 + usize::from(pin.pin());
            assert!(!seen[slot], "{square} collides on expander pin {slot}");
            seen[slot] = true;
        }
        assert!(seen.into_iter().all(|used| used));
    }

    #[test]
    fn expanders_cover_sixteen_squares_each() {
        let mut counts = [0_u8; 4];
        for square in Square::all() {
            counts[usize::from(expander_pin(square).device())] += 1;
        }
        assert_eq!(counts, [16, 16, 16, 16]);
    }

    #[test]
    fn addresses_run_consecutively_from_the_base() {
        let addresses: [u8; 4] = core::array::from_fn(|device| {
            ExpanderPin {
                device: device as u8,
                pin: 0,
            }
            .address()
        });
        assert_eq!(addresses, [0x20, 0x21, 0x22, 0x23]);
    }

    #[test]
    fn quadrant_zero_reads_the_a1_corner() {
        // Matches expander_quadrant("A1-D4") in the electronics naming module.
        for square in Square::all() {
            let inside = file_of(square) < 4 && rank_of(square) < 4;
            assert_eq!(inside, expander_pin(square).device() == 0, "{square}");
        }
    }

    #[test]
    fn port_a_takes_the_lower_two_ranks_of_a_quadrant() {
        for square in Square::all() {
            let pin = expander_pin(square);
            assert_eq!(pin.is_port_b(), rank_of(square) % 4 >= 2, "{square}");
        }
    }

    #[test]
    fn every_square_owns_a_distinct_led_position() {
        let mut seen = [false; 64];
        for square in Square::all() {
            let index = usize::from(led_index(square));
            assert!(!seen[index], "{square} collides at LED {index}");
            seen[index] = true;
        }
        assert!(seen.into_iter().all(|used| used));
    }

    #[test]
    fn the_chain_starts_at_a1_and_snakes_by_rank() {
        assert_eq!(led_index(Square::A1), 0);
        assert_eq!(led_index(Square::H1), 7);
        // Rank 2 runs the other way, so h2 is next after h1.
        assert_eq!(led_index(Square::H2), 8);
        assert_eq!(led_index(Square::A2), 15);
        assert_eq!(led_index(Square::A8), 63);
    }

    #[test]
    fn led_index_round_trips() {
        for square in Square::all() {
            assert_eq!(square_at_led_index(led_index(square)), Some(square));
        }
        assert_eq!(square_at_led_index(64), None);
    }

    #[test]
    fn consecutive_chain_positions_are_adjacent_squares() {
        // A serpentine's whole point: no long jump between neighbours.
        for index in 0..63_u8 {
            let here = square_at_led_index(index).unwrap();
            let next = square_at_led_index(index + 1).unwrap();
            let file_step = file_of(here).abs_diff(file_of(next));
            let rank_step = rank_of(here).abs_diff(rank_of(next));
            assert!(
                file_step + rank_step == 1,
                "{here} to {next} is not a single step"
            );
        }
    }
}
