# Project documentation

This directory contains design and development documentation that spans multiple
code or hardware areas. Component-local instructions stay with their component.

- [`architecture.md`](architecture.md) — how the parts relate, and why the board
  carries no microcontroller
- [`hardware.md`](hardware.md) — the board: sensing, LEDs, bus assignment
- [`fabrication.md`](fabrication.md) — how Gerbers are generated, and what the
  toolchain does and does not verify
- [`power.md`](power.md) — the 5 V rail and where the current goes
- [`cad.md`](cad.md) — the two printed parts and mechanical conventions
- [`host.md`](host.md) — the software on the Raspberry Pi, including WiFi setup
- [`assembly.md`](assembly.md) — what to order and the order to solder it in
- [`protocol.md`](protocol.md) — bridge-to-adapter messages, not a wire protocol
- [`development.md`](development.md) — the supported repository workflow
