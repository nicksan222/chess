//! Opt-in persistence backends for hosted applications.
//!
//! Enable the `sqlite` feature for [`SqliteStore`]. The headless contracts and
//! typed schema remain available without `std` or a concrete backend.

mod sqlite;

pub use rusqlite;
pub use sqlite::SqliteStore;
