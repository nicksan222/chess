//! Boundary between domain values and the third-party search engine.
//!
//! The adapter translates a restricted player-view snapshot into
//! search-engine values and back. Translation never mutates the game;
//! failures surface as computer errors so synchronous computer polling can
//! report them through the player and session instead of playing a move.

mod board;
mod chess_move;
mod model;

pub(super) use board::to_search_board;
pub(super) use chess_move::from_search_move;

#[cfg(test)]
mod tests;
