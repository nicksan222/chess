#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    reason = "integration-test helpers panic to report a failure"
)]

#[path = "../common/mod.rs"]
mod common;

mod play;
mod random_play;
