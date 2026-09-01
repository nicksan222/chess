# Logger crate

This `no_std` crate is the project's headless logging contract. It performs no
I/O and selects no platform backend. Firmware, the simulator, and tests
implement `Logger` and register one process-wide instance during startup.

Records contain a severity, routing target, source module/file/line, and
allocation-free `core::fmt::Arguments`. The `error!`, `warn!`, `info!`,
`debug!`, `trace!`, and level-selectable `log!` macros evaluate message
arguments only when the backend enables the record.

```rust
use logger::{Logger, Record, info, register};

struct RaspberryPiLogger;

impl Logger for RaspberryPiLogger {
    fn log(&self, record: Record<'_>) {
        // Forward to journald, stderr, a serial adapter, etc.
        let _ = record;
    }
}

static LOGGER: RaspberryPiLogger = RaspberryPiLogger;
register(&LOGGER)?;
info!(target: "firmware", "board ready");
# Ok::<(), logger::RegistrationError>(())
```

Backends own filtering, formatting, synchronization, buffering, and flushing.
`NopLogger` is supplied for callers that deliberately discard all diagnostics.

## Registration

A hosted application can register one static logger during startup:

```rust
use logger::{LevelFilter, implementations::SystemdLogger, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);
register(&LOGGER)?;
# Ok::<(), logger::RegistrationError>(())
```

Shared crates use the same logging macros. Before registration they do nothing,
so logging remains optional. Registration is thread-safe, allocation-free,
`no_std`, and permanent; a different logger cannot replace the first one.

## Hosted implementations

Enable the `std` feature for two implementations kept in this crate:

- `implementations::SystemdLogger` writes syslog-priority-prefixed records to
  stderr, where the Yocto firmware's systemd service captures them in journald;
- `implementations::StderrLogger` writes human-readable records for terminals,
  desktop applications, and the simulator.

They are separate concrete types in separate source files, so their `Logger`
implementations do not overlap or collide. Both default to `LevelFilter::Info`
and accept a different maximum level through `new`.
