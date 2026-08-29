//! Piece-specific legal move generation.

mod application;
mod calculators;
mod forced;
mod generation;

pub use forced::{ForceMoveError, ForcedMove};
