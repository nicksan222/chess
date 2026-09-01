use std::{path::Path, vec::Vec};

use rusqlite::{Connection, OptionalExtension, params};

use crate::{KeyValueStore, LoadOutcome};

const CREATE_TABLE: &str = "
    CREATE TABLE IF NOT EXISTS persistence_values (
        key   BLOB PRIMARY KEY NOT NULL,
        value BLOB NOT NULL
    ) WITHOUT ROWID;
";

/// A SQLite-backed implementation of [`KeyValueStore`].
///
/// Keys and values are stored as SQLite BLOBs without text conversion. Every
/// [`KeyValueStore::store`] and [`KeyValueStore::remove`] call is an individual
/// autocommit transaction unless the consumer starts a transaction directly on
/// the underlying [`Connection`].
///
/// The `sqlite` crate feature uses rusqlite's bundled SQLite build, so consumers
/// do not need a system SQLite development package.
pub struct SqliteStore {
    connection: Connection,
}

impl SqliteStore {
    /// Opens or creates a database at `path` and initializes its value table.
    pub fn open(path: impl AsRef<Path>) -> rusqlite::Result<Self> {
        Self::from_connection(Connection::open(path)?)
    }

    /// Opens an isolated in-memory database and initializes its value table.
    pub fn in_memory() -> rusqlite::Result<Self> {
        Self::from_connection(Connection::open_in_memory()?)
    }

    /// Wraps a connection and initializes the value table if necessary.
    ///
    /// This constructor lets applications configure pragmas, URI parameters,
    /// encryption, or connection flags before creating the store.
    pub fn from_connection(connection: Connection) -> rusqlite::Result<Self> {
        connection.execute_batch(CREATE_TABLE)?;
        Ok(Self { connection })
    }

    /// Borrows the underlying SQLite connection.
    #[must_use]
    pub const fn connection(&self) -> &Connection {
        &self.connection
    }

    /// Mutably borrows the underlying SQLite connection.
    pub const fn connection_mut(&mut self) -> &mut Connection {
        &mut self.connection
    }

    /// Returns the underlying SQLite connection.
    #[must_use]
    pub fn into_connection(self) -> Connection {
        self.connection
    }

    fn value(&self, key: &[u8]) -> rusqlite::Result<Option<Vec<u8>>> {
        self.connection
            .query_row(
                "SELECT value FROM persistence_values WHERE key = ?1",
                params![key],
                |row| row.get(0),
            )
            .optional()
    }
}

impl KeyValueStore for SqliteStore {
    type Error = rusqlite::Error;

    fn value_len(&mut self, key: &[u8]) -> Result<Option<usize>, Self::Error> {
        let length = self
            .connection
            .query_row(
                "SELECT length(value) FROM persistence_values WHERE key = ?1",
                params![key],
                |row| row.get::<_, i64>(0),
            )
            .optional()?;
        length
            .map(|value| {
                usize::try_from(value)
                    .map_err(|_| rusqlite::Error::IntegralValueOutOfRange(0, value))
            })
            .transpose()
    }

    fn load(&mut self, key: &[u8], output: &mut [u8]) -> Result<LoadOutcome, Self::Error> {
        let Some(value) = self.value(key)? else {
            return Ok(LoadOutcome::NotFound);
        };
        if output.len() < value.len() {
            return Ok(LoadOutcome::BufferTooSmall {
                required: value.len(),
            });
        }

        output[..value.len()].copy_from_slice(&value);
        Ok(LoadOutcome::Loaded { len: value.len() })
    }

    fn store(&mut self, key: &[u8], value: &[u8]) -> Result<(), Self::Error> {
        self.connection.execute(
            "INSERT INTO persistence_values (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            params![key, value],
        )?;
        Ok(())
    }

    fn remove(&mut self, key: &[u8]) -> Result<bool, Self::Error> {
        self.connection
            .execute(
                "DELETE FROM persistence_values WHERE key = ?1",
                params![key],
            )
            .map(|changed| changed != 0)
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        // SQLite commits each write before `execute` returns in autocommit mode.
        // Explicit transactions remain under the consumer's control.
        Ok(())
    }
}
