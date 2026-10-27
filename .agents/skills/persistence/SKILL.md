---
name: persistence
description: The purpose and outside view of the `persistence` crate, the project's contract for remembering things across restarts. Use when code needs to save or load settings or data, or when choosing how and where something is stored.
---

Read the [crate README](../../../crates/persistence/README.md) and [source](../../../crates/persistence/src/) for current contracts and APIs.

Consumers own keys, encodings, versions and migrations. Changes to stored keys, value encodings or record envelopes cross a migration boundary.
