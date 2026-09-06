# Native KiCad board as Python

Start at [`definition/board.py`](definition/board.py): power, controls, 64 squares,
eight Hall banks, and the serpentine LED chain. `load()` returns a **pcbnew.BOARD**.
There is no parallel PCB model, geometry enum, placement aggregate, or adapter.
Python generates the board automatically; editing generated files is not authoring.

```text
definition/
  board.py, native.py, rules.py  Composition, native construction helpers, constraints
  assemblies/                   Power, controls, square, sensor-bank wiring
  parts/                        Approved native FOOTPRINT/PAD templates
  routing/                      Native routing policies and grid pathfinding
  output/                       Schematic, BOM/project, symbols, review markings
  evidence/                     Human prototype measurements (not generated)
tests/                          Focused mechanics/build checks and SPICE scenarios
generated/                      Native project, expanded netlist, BOM, reports/previews
typings/                        Curated KiCad SWIG API signatures for strict Pyright
```

The fourth top-level folder is typing declarations only, not another implementation
of KiCad geometry. Subpackages organize responsibilities; their `__init__.py` files
do not provide wrapper APIs.

## Authoring and authority

`pcbnew` owns footprints, pads, placement, layers, nets, tracks, zones, and geometry.
Shared dimensions, approved products, pin enums, GPIO assignments and Hall-bank
mappings remain inputs from `hardware/shared/`. Small assembly handles expose shared
logical ports only. `place()` installs a native template and `connect()` assigns its
native pads from component-bound pins, rejecting duplicate ownership or reassignment.
There is no finish/freeze framework. Runtime validation checks approved products,
complete pad assignment, square membership/centres and Hall-bank wiring.

Board properties retain assembly/product intent. BOM, expanded netlist and schematic
are derived from the actual native footprints and pad assignments, not a second
connectivity graph. `generated/netlist.json` is output only. Native coordinate helpers
translate shared centre-origin/Y-up dimensions; dimension tests check against CAD.

References and historical LED net names are explicit. Native UUIDs are semantic,
reference/geometry-derived, with stable disambiguation for identical items. The
intentional one-time UUID rekey preserves physical geometry and connectivity, and
footprint paths link to generated schematic symbols. No frozen identity ledger exists.

## Commands

Python 3.12+, KiCad 9, ngspice, Ruff 0.16.5 and Pyright 1.1.411 are installed in the
development container. From the repository root:

```sh
just --justfile hardware/pcb/justfile generate # Native project, schematic, BOM, DSN
just --justfile hardware/pcb/justfile check    # Non-publishing source/dimensions checks
just --justfile hardware/pcb/justfile review   # Fresh ERC/DRC, tests/SPICE, previews
just --justfile hardware/pcb/justfile release  # Review + measured evidence + fabrication
```

Direct entry: `PYTHONPATH=hardware python3 -m pcb review`. Set `PYRIGHT` to an
alternate analyzer executable when needed.

**Deliberate scope reductions:** redundant architecture/accessor/snapshot tests were
removed in favor of readable dimensions and SPICE tests. PCB-to-Rust generation and
its parity plumbing were removed at user request. Firmware pin declarations in
`apps/firmware/src/hardware/pins/` are hand-maintained; there is no `pins` command.

Run retained tests without publishing: `PYTHONPATH=hardware python3 -m unittest
discover -s hardware/pcb/tests -p 'test_*.py'`. SPICE covers all squares/buttons,
open-drain buses, level shifting, startup/off/approved/full-white power, and quiet,
capture, castling, en-passant and promotion moves. Circuit files are staged under
`generated/spice/`, or temporary in standalone runs.

## Review and release

Open `generated/chess-board.kicad_pro`. The schematic has an overview, power,
controls and eight bank sheets; each bank groups complete squares. Passives have
recognizable symbols; active pins carry conservative electrical roles.

`review` requires zero native ERC/DRC violations, unconnected items and schematic
parity differences, plus the retained tests/SPICE. It exports positions, SVGs and
board renders. `review.md`, `layout.json` and `manifest.json` record changes, checks,
source/tool hashes and artifact hashes for that exact build.

Writers use a lock and sibling staging directory. Failure preserves the previous
output set; successful publication replaces the whole directory with rename rollback.
Readers never see mixed old/new files, although the directory may briefly be absent
between renames. Stale reports and fabrication exports disappear with replacement.

`release` additionally validates real Hall/magnet measurements through
`build.physical_evidence()` **before fabrication export**. Missing evidence deliberately
blocks Gerbers and separate plated/non-plated Excellon drills/slots. No test skip or
software check substitutes for those measurements. See [`definition/evidence/`](definition/evidence/).
