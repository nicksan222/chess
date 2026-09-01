# Logger crate

This `no_std` crate is the project's headless logging contract. It performs no
I/O, owns no global state, and selects no platform backend. Firmware, the
simulator, and tests implement `Logger` and explicitly pass that value to the
code they run.

Records contain a severity, routing target, source module/file/line, and
allocation-free `core::fmt::Arguments`. The `error!`, `warn!`, `info!`,
`debug!`, `trace!`, and level-selectable `log!` macros evaluate message
arguments only when the backend enables the record.

```rust
use logger::{Logger, Record, info};

struct RaspberryPiLogger;

impl Logger for RaspberryPiLogger {
    fn log(&self, record: Record<'_>) {
        // Forward to journald, stderr, a serial adapter, etc.
        let _ = record;
    }
}

let logger = RaspberryPiLogger;
info!(logger, target: "firmware", "board ready");
```

Backends own filtering, formatting, synchronization, buffering, and flushing.
`NopLogger` is supplied for callers that deliberately discard all diagnostics.

## Hosted implementations

Enable the `std` feature for two implementations kept in this crate:

- `implementations::SystemdLogger` writes syslog-priority-prefixed records to
  stderr, where the Yocto firmware's systemd service captures them in journald;
- `implementations::StderrLogger` writes human-readable records for terminals,
  desktop applications, and the simulator.

They are separate concrete types in separate source files, so their `Logger`
implementations do not overlap or collide. Both default to `LevelFilter::Info`
and accept a different maximum level through `new`.
