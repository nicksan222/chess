---
name: logger
description: The purpose and outside view of the `logger` crate, the project's single, optional way to say what happened. Use when emitting diagnostics from any crate or wiring logging into an application.
---

# logger

## What it is for

The logger crate is a contract, not a destination. It lets any part of the
system say what happened without knowing where the words end up. On the Pi
they reach journald; in a terminal they reach stderr; in a pure library test
they go nowhere.

## How it thinks

- **Speaking is separate from listening.** Libraries only emit records. The
  application decides, once, who listens.
- **One listener, chosen once.** The first logger registered stays for the
  life of the process. Nothing can quietly replace it later.
- **Logging is optional and free when off.** Before anyone registers, every
  log call does nothing, and message arguments are not even evaluated. A
  library can log freely without forcing a backend on its users.
- **The backend owns policy.** Filtering, formatting, buffering and
  durability are the listener's business, not the speaker's.

## Using it from outside

- In a library: use `error!`, `warn!`, `info!`, `debug!` and `trace!`, with
  a `target:` when the source should be clear. Never register a logger.
- In an application: register one static logger at startup, such as the
  ready-made `SystemdLogger` for the Pi service or `StderrLogger` for
  development (both need the `std` feature), or your own `Logger`.
- Use `NopLogger` when discarding diagnostics is an explicit choice.
- Keep backends safe: a logger must not panic or log through itself.

## Where things belong

What gets logged belongs to each crate, and when and where logging is
enabled belongs to the application. Only the shared shape of a log record
and the single place it is delivered belong here.
