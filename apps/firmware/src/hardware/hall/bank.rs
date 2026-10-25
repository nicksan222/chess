//! Which squares each Hall-sensor expander reads, and on which channel.
//!
//! Hand-maintained mirror of `hardware/shared/hall_banks.py`;
//! `hardware/shared/tests/test_firmware_hall_banks.py` parses this table and
//! fails if it disagrees with the contract.

use crate::hardware::{BoardPosition, square};

/// Seven-bit I2C address of bank zero; bank `n` answers at `FIRST_ADDRESS + n`.
pub const FIRST_ADDRESS: u8 = 0x20;

/// A table of square names, checked at compile time.
macro_rules! banks {
    ($([$($square:ident),+ $(,)?]),+ $(,)?) => {
        [$([$(square!($square)),+]),+]
    };
}

/// The square on each expander channel, one row per bank in address order:
/// left to right, then bottom to top. Each bank reads a 4-file by 2-rank block;
/// P0–P3 serve its left half and P4–P7 its right.
const BANKS: [[BoardPosition; HallBank::CHANNELS]; HallBank::COUNT] = banks![
    //P0 P1  P2  P3  P4  P5  P6  P7
    [A1, B1, A2, B2, C1, D1, C2, D2],
    [E1, F1, E2, F2, G1, H1, G2, H2],
    [A3, B3, A4, B4, C3, D3, C4, D4],
    [E3, F3, E4, F4, G3, H3, G4, H4],
    [A5, B5, A6, B6, C5, D5, C6, D6],
    [E5, F5, E6, F6, G5, H5, G6, H6],
    [A7, B7, A8, B8, C7, D7, C8, D8],
    [E7, F7, E8, F8, G7, H7, G8, H8],
];

/// One TCA9554 expander and the block of squares it reads.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HallBank {
    index: u8,
}

impl HallBank {
    /// Number of expanders on the board.
    pub const COUNT: usize = 8;
    /// Input channels on one expander, one per square.
    pub const CHANNELS: usize = 8;

    /// Every bank, in the address order the board is scanned.
    pub fn all() -> [Self; Self::COUNT] {
        std::array::from_fn(|index| Self { index: index as u8 })
    }

    pub const fn address(self) -> u8 {
        FIRST_ADDRESS + self.index
    }

    /// The squares on channels P0–P7.
    pub const fn squares(self) -> &'static [BoardPosition; Self::CHANNELS] {
        &BANKS[self.index as usize]
    }

    /// Diagonal-corner name such as "A1-D2", matching the contract's labels.
    pub fn label(self) -> String {
        let squares = self.squares();
        format!("{}-{}", squares[0], squares[Self::CHANNELS - 1])
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashSet;

    use super::*;

    #[test]
    fn banks_cover_every_square_exactly_once() {
        let squares: HashSet<_> = BANKS.iter().flatten().collect();
        assert_eq!(squares.len(), 64);
    }

    #[test]
    fn each_bank_is_a_four_by_two_block_split_into_halves() {
        for bank in HallBank::all() {
            let [origin, ..] = bank.squares();
            for (channel, square) in bank.squares().iter().enumerate() {
                let (half, row, column) = (channel / 4, channel / 2 % 2, channel % 2);
                assert_eq!(usize::from(square.row() - origin.row()), row);
                assert_eq!(
                    usize::from(square.column() - origin.column()),
                    half * 2 + column
                );
            }
        }
        assert_eq!(HallBank::all()[3].label(), "E3-H4");
    }

    #[test]
    fn addresses_are_consecutive_from_the_first_strap() {
        let addresses = HallBank::all().map(HallBank::address);
        assert_eq!(addresses, [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27]);
    }
}
