//! Integration-neutral model of the physical board.
//!
//! This crate is where the board's wiring becomes chess vocabulary. It knows
//! that a square is read by a particular pin on a particular I2C expander and
//! lit by a particular position in the LED chain, and it knows how to turn a
//! stream of raw expander reads into settled, debounced changes.
//!
//! It deliberately knows nothing about how those reads are obtained. There is no
//! I2C, no SPI and no operating system here, so the mapping can be tested on a
//! host without any hardware present.
//!
//! The mappings must agree with `hardware/shared/wiring.py`, the
//! tool-independent hardware contract.

#![no_std]
#![forbid(unsafe_code)]

mod debounce;
mod mapping;
mod occupancy;

pub use debounce::{Debouncer, SquareChange};
pub use mapping::{
    EXPANDER_BASE_ADDRESS, EXPANDER_COUNT, ExpanderPin, PINS_PER_EXPANDER, expander_pin, led_index,
    square_at_led_index,
};
pub use occupancy::Occupancy;

/// Number of squares on the board, and so of Hall sensors and LEDs.
pub const SQUARE_COUNT: usize = 64;
