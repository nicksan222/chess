# Chess

Chess aims to become an open-source physical smart chessboard. The intended
board combines 64 magnetic square sensors and 64 individually addressable RGB
LEDs with a battery-powered Raspberry Pi Pico 2 W.

The firmware will be written in Rust for the RP2350's ARM Cortex-M33 and is
expected to use Embassy in the future. Initial development is focused on
offline chess functionality: physical board sensing, lighting, local play, and
the shared models needed to support them. Integration points remain isolated so
additional adapters can be introduced later without changing board logic.

This repository currently contains scaffolding only. No firmware, chess logic,
protocol, bridge integration, or simulator behavior has been implemented.
Shared Rust crates, firmware, bridge and simulator applications, Blender source,
electronics documentation, the bill of materials, and project documentation
all live in this monorepo.

See [docs/development.md](docs/development.md) for the current host-side checks.
