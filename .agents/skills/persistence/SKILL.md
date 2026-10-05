---
name: persistence
description: The purpose and outside view of the `persistence` crate, the project's contract for remembering things across restarts. Use when code needs to save or load settings or data, or when choosing how and where something is stored.
---

# persistence

## What it is for

The persistence crate describes *how to remember* without deciding *where*.
It defines a small byte-level storage contract and a typed layer on top, so
domain code can save a setting without knowing whether it lands in SQLite,
flash, a file or a test double.

## How it thinks

- **Storage is injected, never global.** Unlike logging, persistence is a
  real dependency. Code that needs a store receives one, which allows
  separate stores, transactions and isolated tests.
- **Keys and types live together.** A schema names each key and its value
  type in one place owned by the consumer, so a value cannot be read back as
  the wrong type and duplicate keys are rejected at compile time.
- **Stored bytes are promises.** Keys, value encodings and the record
  envelope outlive the code that wrote them. Changing them is a migration,
  not a refactor.
- **The domain owns meaning.** This crate provides codecs, an optional
  versioned and checksummed envelope, and a SQLite backend. What gets stored,
  under which version, and how old data migrates are the consumer's
  decisions.

## Using it from outside

- Declare your keys with `persistence_schema!` in your own crate, and use
  `save!` and `retrieve!` against a store you were given.
- Implement `EncodeValue` and `DecodeValue` for your own types. Built-in
  stable encodings already cover integers, byte arrays, `bool`, `Toggle` and
  `Percentage`.
- Use `record` when data needs a schema version and corruption detection.
- On hosted systems, enable the `sqlite` feature for a ready-made
  `SqliteStore`; elsewhere, implement `KeyValueStore` for your medium.
- The backend owns durability, capacity and synchronization.

## Where things belong

Choosing a database and deciding what to save belong to the application.
Only the shared rules for turning typed values into durable bytes belong
here.
