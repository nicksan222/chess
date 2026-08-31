# KiCad PCB

The board is a native KiCad 9 project composed from Python:

- `generate.py` builds `chess-board.kicad_pcb` through KiCad's `pcbnew` API.
- `design/netlist.json` is the reviewed connectivity contract.
- `core/placement.py` and `footprints/` implement placement and package geometry.
- `hardware/shared/` supplies dimensions, component identities, and wiring.
- `chess-board.kicad_pro` and `chess-board.kicad_pcb` open directly in KiCad.

Run `./tools/pcb` to regenerate the project, run KiCad DRC, and export Gerber,
drill, and SVG artifacts into `generated/`.

## Routing status

The migration intentionally discarded the old custom traces because KiCad DRC
proved they crossed unrelated pads. The generated board currently begins with a
complete netlist and placement but no trusted routing. `generated/drc.rpt` is the
authoritative work list. Do not order boards until it reports zero violations and
zero unconnected items.

Routing edits made only in the generated board are overwritten. Reusable routing
or zones must be represented by generator code before regeneration.
