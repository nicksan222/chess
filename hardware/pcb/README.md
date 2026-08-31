# KiCad PCB

The board is a native KiCad 9 project composed from Python:

- `generate.py` builds `chess-board.kicad_pcb` through KiCad's `pcbnew` API.
- `design/netlist.json` is the reviewed connectivity contract.
- `core/placement.py` and `footprints/` implement placement and package geometry.
- `hardware/shared/` supplies dimensions, component identities, and wiring.
- `chess-board.kicad_pro` and `chess-board.kicad_pcb` open directly in KiCad.

Run `./tools/pcb` to regenerate the project, run KiCad DRC, and export Gerber,
drill, and SVG artifacts into `generated/`.
