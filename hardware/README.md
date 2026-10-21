# Hardware

This directory contains the manufacturable PCB and the mechanical design around it:

- **`pcb/`** — the board's specification in `spec/` (approved parts, typed pins,
  wiring, Hall banks, board geometry and the Pi placement), reviewed connectivity,
  bill of materials, footprints, placement, routing, Gerber and Excellon output.
- **`cad/`** — printable enclosure and tile plate generated with Blender, with
  their own dimensions in `cad/dimensions/`.

Data flows one way. The PCB build exports the board interface (outline, squares,
mounting holes, Pi, panel products and harness) in
`pcb/generated/pcb-components.json` beside the KiCad model. CAD geometry reads only
that export; CAD tests rebuild it from the current PCB to catch a stale export. To
move something on the board, change the PCB and regenerate it; CAD follows.

There is intentionally no separate electronics/schematic domain. The PCB is the
electrical design, and `pcb/board/board.py` composes its explicit connectivity
contract from typed components through the harness. The expanded netlist is generated output. Run `just --justfile hardware/pcb/justfile review` to validate and generate review and fabrication files. Manufacturing approval remains pending; `release` refuses approval.
