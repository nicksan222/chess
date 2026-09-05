//! Local computer player backed by the open-source `chess-engine` crate.

mod adapter;
mod difficulty;
mod error;
mod source;

pub use difficulty::Difficulty;
pub use error::ComputerError;
pub(super) use source::Computer;
