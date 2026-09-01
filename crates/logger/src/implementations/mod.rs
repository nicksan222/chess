//! Ready-made hosted logging backends.
//!
//! These implementations are available with the `std` feature. They are
//! separate concrete types, so applications can depend on both without
//! conflicting trait implementations.

mod stderr;
mod systemd;

pub use stderr::StderrLogger;
pub use systemd::SystemdLogger;
