//! SHA-256 board anchoring, event hashing, and link validation.

#[macro_use]
mod writer;
mod anchor;
mod error;
mod event;
mod status;
#[cfg(test)]
mod tests;
mod validation;

pub(super) use anchor::calculate_board_anchor;
pub(super) use event::calculate_hash;
pub(super) use validation::validate_step;
