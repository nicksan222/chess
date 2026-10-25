#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    reason = "integration-test helpers panic to report a failure"
)]

mod facade;
#[cfg(feature = "std")]
mod implementations;
mod level;
mod record;
