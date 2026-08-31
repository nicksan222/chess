# Hardware

This directory contains electronics, board layout and mechanical design sources,
all generated from Python with no EDA or CAD application in the loop. Tool-independent definitions live in **`shared/`**, and each domain adapts them to its own output format:

- **`electronics/`** — schematics drawn with Schemdraw, plus a bill of materials
  and a netlist counted from the placed symbols.
- **`pcb/`** — the board's Gerber and Excellon artwork, written directly with
  Gerbonara. Reads the netlist the schematic publishes, so run electronics first.
- **`cad/`** — the two printable parts, generated with Blender.

All three have the same shape and the same runner contract, so `./tools/cad`,
`./tools/electronics` and `./tools/pcb` do the same sequential job: install if
needed, test, then generate.

There is no firmware directory. The board carries no microcontroller — a
Raspberry Pi Zero 2 W reads the sensors and drives the LEDs directly, so the
software that runs the board is an ordinary host program in `apps/bridge`. See
[`../docs/architecture.md`](../docs/architecture.md).
