//! A tiny, headless logging facade with optional global registration.
//!
//! This crate performs no I/O by itself. Applications implement [`Logger`] for
//! their platform and permanently [`register`] one shared instance. [`get`]
//! returns `None` until registration. Messages are allocation-free
//! [`core::fmt::Arguments`], making the same interface suitable for a Raspberry
//! Pi, development tool, or test double.
//! The optional `std` feature supplies ready-made stderr and systemd backends
//! under [`implementations`].
//!
//! ```
//! use logger::{Level, Logger, Record, info, register};
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
//! static LOGGER: Sink = Sink;
//! register(&LOGGER)?;
//! info!("ready");
//! # Ok::<(), logger::RegistrationError>(())
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
mod registry;

#[macro_use]
mod macros;

pub use level::{Level, LevelFilter};
pub use logger::{Logger, NopLogger};
pub use metadata::Metadata;
pub use record::Record;
pub use registry::{RegistrationError, flush, get, register};
