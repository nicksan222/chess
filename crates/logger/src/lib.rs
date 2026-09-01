//! A tiny, headless logging facade with explicit dependency injection.
//!
//! This crate owns no global logger and performs no I/O. Applications implement
//! [`Logger`] for their platform and pass that implementation to code which
//! emits records. Messages are allocation-free [`core::fmt::Arguments`], making
//! the same interface suitable for a Raspberry Pi, simulator, or test double.
//! The optional `std` feature supplies ready-made stderr and systemd backends
//! under [`implementations`].
//!
//! ```
//! use logger::{Level, Logger, Metadata, Record, info};
//!
//! struct Sink;
//!
//! impl Logger for Sink {
//!     fn log(&self, record: Record<'_>) {
//!         assert_eq!(record.level(), Level::Info);
//!         assert_eq!(record.arguments().as_str(), Some("ready"));
//!     }
//! }
//!
//! info!(Sink, "ready");
//! ```

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

#[cfg(feature = "std")]
extern crate std;

#[cfg(feature = "std")]
pub mod implementations;

mod level;
mod logger;
mod metadata;
mod record;

#[macro_use]
mod macros;

pub use level::{Level, LevelFilter};
pub use logger::{Logger, NopLogger};
pub use metadata::Metadata;
pub use record::Record;
