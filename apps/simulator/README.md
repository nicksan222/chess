# Simulator application

This application owns host-side virtual board and simulation tooling for
deterministic development and CI validation. Reusable board and protocol concepts
belong in shared crates rather than being duplicated here.

There is no embedded target to cross-compile for; the board carries no
microcontroller. Hardware-in-the-loop testing against a real board is a possible
future direction, but the mapping in `crates/board-model` is already testable on
a host without one.
