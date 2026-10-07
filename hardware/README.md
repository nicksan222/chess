# Hardware

This directory contains the shared physical contract, manufacturable PCB, and
mechanical design:

- **`shared/`** — tool-independent dimensions, component identities, wiring,
  mappings, and host GPIO assignments.
- **`pcb/`** — reviewed connectivity, bill of materials, footprints, placement,
  routing, Gerber and Excellon fabrication output.
- **`cad/`** — printable enclosure and tile plate generated with Blender.

There is intentionally no separate electronics/schematic domain. The PCB is the
electrical design, and `pcb/board/board.py` composes its explicit connectivity
contract from typed components through the harness. The expanded netlist is generated output. Run `just --justfile hardware/pcb/justfile review` to validate and generate review and fabrication files. Manufacturing approval remains pending; `release` refuses approval.
