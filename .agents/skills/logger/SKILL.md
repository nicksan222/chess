---
name: logger
description: The purpose and outside view of the `logger` crate, the project's single, optional way to say what happened. Use when emitting diagnostics from any crate or wiring logging into an application.
---

Read the [crate README](../../../crates/logger/README.md) and [source](../../../crates/logger/src/) for current contracts and APIs.

Libraries emit diagnostics; the application chooses and registers the backend. A backend must not panic or log through itself, which would recurse.
