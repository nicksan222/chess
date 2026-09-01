# Persistence crate

This `no_std` crate is the project's headless persistence contract. It performs
no I/O, selects no database, and requires no allocator. Firmware, backend,
simulator, and tests provide their own `KeyValueStore` implementations and
inject them into the code that needs persistence.

The deliberately small byte-oriented backend API can be adapted to embedded
flash, files, SQLite, remote storage, or an in-memory test double without
forcing those concerns onto shared domain crates. Above it, a typed schema keeps
keys and value types in one consumer-owned inventory:

```rust
use chess_core::{Percentage, Toggle};
use persistence::{persistence_schema, retrieve, save};

persistence_schema! {
    pub struct Settings {
        pub sound: Toggle = b"settings/sound",
        pub brightness: Percentage = b"settings/brightness",
    }
}

// Given an application-supplied `store`:
// save!(&mut store, Settings::new().sound, Toggle::On)?;
// let sound: Option<Toggle> = retrieve!(&mut store, Settings::new().sound)?;
```

`Field<T>` prevents retrieving `sound` as any type other than `Toggle`. Schema
keys are checked for emptiness and duplicates during compilation. Built-in
stable codecs cover integers, byte arrays, `bool`, `Toggle`, and `Percentage`;
consumers implement `EncodeValue` and `DecodeValue` for their own domain values.
Small `InlineValue` codecs create their scratch buffer on the stack; variable-
length codecs accept an explicit caller-owned buffer.

Implementations own synchronization, durability, transactions, capacity limits,
and backend error types. Domain code owns keys, custom payload formats, schema
versions, and migrations. `record` provides an allocation-free versioned and
checksummed byte envelope when that common framing is useful.

There is intentionally no global registry: unlike diagnostics, persistence is a
domain dependency, and explicit injection permits separate stores, transactions,
and isolated tests.

## SQLite backend

Enable the opt-in `sqlite` feature to use
`implementations::SqliteStore`. It stores binary keys and values without text
conversion, initializes its table automatically, supports caller-controlled
SQLite transactions, and uses bundled SQLite so no system development package
is required:

```toml
persistence = { path = "../persistence", features = ["sqlite"] }
```

```rust
use persistence::implementations::SqliteStore;

let store = SqliteStore::open("application.sqlite3")?;
# Ok::<(), persistence::implementations::rusqlite::Error>(())
```
