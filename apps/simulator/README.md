# Simulator application

This application owns host-side virtual board and simulation tooling for
deterministic development and CI validation. Reusable board and protocol concepts
belong in shared crates rather than being duplicated here.

Embedded validation may also use cross-compilation or hardware-in-the-loop
testing when those approaches have concrete requirements.
