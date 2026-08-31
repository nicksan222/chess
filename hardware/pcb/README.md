# KiCad PCB

The board is a native KiCad 9 project composed from Python:

- `write_schematic.py` builds the native schematic and embedded symbol library.
- `generate.py` builds the eight-layer `chess-board.kicad_pcb` through KiCad's
  `pcbnew` API: three rail planes, three isolated bus layers, and two outer
  routing layers.
- `design/netlist.json` is the reviewed connectivity contract; every placed
  component references an approved `part_key`.
- `design/bom.md` is generated with exact manufacturer part numbers from
  `hardware/shared/components.py`; anonymous substitutions are rejected.
- `core/placement.py` and `footprints/` implement placement and package geometry.
- `hardware/shared/` supplies dimensions, component identities, and wiring.
- `chess-board.kicad_pro`, `chess-board.kicad_sch`, and
  `chess-board.kicad_pcb` open directly in KiCad.

Run `./tools/pcb` to regenerate the exact-MPN BOM and native project, run KiCad
DRC, audit every release dimension, and produce fitted SVG and high-quality 3D
review renders in `generated/`. `AUDIT.md` is the human blocking-work list;
`generated/audit.json` is its machine-readable status.

## Non-negotiable release policy

The runner removes stale fabrication files before validation. Gerber and drill
output is recreated only when all of these are true:

- KiCad reports zero ERC/DRC violations and zero unconnected items;
- the project contains no DRC exclusions;
- every intentionally unused pin is explicitly marked `no_connect` in the
  reviewed connectivity contract;
- there are no PCB/schematic parity errors;
- reed/magnet prototype evidence exists in `prototype/`.

`validate_release.py` enforces the policy after review images are generated and
before fabrication export. A failed gate is a failed build, not a warning.
