#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    reason = "integration-test helpers panic to report a failure"
)]

mod board;
mod chess_move;
mod piece;
mod square;
mod square_set;
