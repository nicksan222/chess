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

## Container operations

The PCB-local `Makefile` is the supported entry point from a host machine. Every
board operation executes in the reproducible KiCad 9 development container, so
host Python or KiCad versions cannot silently change the output:

```sh
make -C hardware/pcb help             # list all operations
make -C hardware/pcb test             # fast composition tests
make -C hardware/pcb component-audit  # exact products, semantic pins, footprints
make -C hardware/pcb board            # regenerate native sources
make -C hardware/pcb review           # generation + ERC/DRC/parity/renders, no Gerbers
make -C hardware/pcb status           # print generated/audit.json
make -C hardware/pcb release          # gated fabrication export
make -C hardware/pcb shell            # container shell
make -C hardware/pcb down             # remove the container
```

`make release` runs `./tools/pcb`; it is not a shortcut around the release gate.
`AUDIT.md` is the human blocking-work list and `generated/audit.json` is its
machine-readable status.

## Product reality and readiness

Every fitted electrical part resolves to an explicit manufacturer and part
number in `hardware/shared/components.py`. The component-model tests require
that each product has a semantic pin enum and that its logical pins exactly
match its footprint. The generated BOM therefore contains purchasable product
identities rather than anonymous `R`, `C`, or connector placeholders.

That does **not** make the board automatically production-ready. Availability,
manufacturer drawing review, stack-up review, component 3D models, and physical
reed/magnet validation remain real engineering gates. The repository currently
reports `release_ready: false` because prototype evidence is absent; do not order
the board until `make -C hardware/pcb release` succeeds without bypasses.

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
