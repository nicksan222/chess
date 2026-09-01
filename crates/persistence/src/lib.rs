//! Headless persistence contracts shared across applications and platforms.
//!
//! This crate performs no I/O and chooses no database. Applications implement
//! [`KeyValueStore`] for embedded flash, files, SQLite, a remote service, or a
//! test double, then inject that implementation where it is needed. Values are
//! byte slices and loads use caller-provided buffers, so the contract requires
//! neither `std` nor allocation.
//!
//! [`persistence_schema!`] lets each consumer declare one struct containing all
//! of its typed fields. [`save!`] and [`retrieve!`] then encode or decode through
//! those fields without allowing a key to be requested as the wrong type. The
//! independent [`record`] helpers provide versioned, checksummed envelopes when
//! domain code needs them.
//!
//! ```
//! use core::convert::Infallible;
//! use persistence::{KeyValueStore, LoadOutcome};
//!
//! struct FirmwareStore;
//!
//! impl KeyValueStore for FirmwareStore {
//!     type Error = Infallible;
//!
//!     fn value_len(&mut self, _key: &[u8]) -> Result<Option<usize>, Self::Error> {
//!         Ok(None)
//!     }
//!
//!     fn load(
//!         &mut self,
//!         _key: &[u8],
//!         _output: &mut [u8],
//!     ) -> Result<LoadOutcome, Self::Error> {
//!         Ok(LoadOutcome::NotFound)
//!     }
//!
//!     fn store(&mut self, _key: &[u8], _value: &[u8]) -> Result<(), Self::Error> {
//!         Ok(())
//!     }
//!
//!     fn remove(&mut self, _key: &[u8]) -> Result<bool, Self::Error> {
//!         Ok(false)
//!     }
//!
//!     fn flush(&mut self) -> Result<(), Self::Error> {
//!         Ok(())
//!     }
//! }
//! ```

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

#[cfg(feature = "std")]
extern crate std;

#[cfg(feature = "sqlite")]
pub mod implementations;

#[macro_use]
mod macros;

pub mod record;
pub mod schema;
mod store;
pub mod value;

pub use schema::{Field, RetrieveError, SaveError};
pub use store::{KeyValueStore, LoadOutcome};
pub use value::{DecodeValue, EncodeValue, InlineValue, ValueDecodeError, ValueEncodeError};
