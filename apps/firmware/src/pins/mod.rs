//! Raspberry Pi GPIO assignments for the chess board.
//!
//! Keep this map in sync with `hardware/shared/wiring.py`. BCM numbers are
//! Linux GPIO line offsets, not physical header positions.

mod backend;
mod board;
mod capability;
mod gpio;
mod pin;

pub use backend::{Level, OutputBackend};
pub use board::BoardPins;
pub use capability::{Capability, CapabilityKind, Input, InputOutput, Output, Readable, Writable};
pub use gpio::Gpio;
pub use pin::Pin;
