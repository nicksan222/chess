#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    reason = "integration-test helpers panic to report a failure"
)]

mod common;
mod record;
mod schema;
mod store;
mod value;
