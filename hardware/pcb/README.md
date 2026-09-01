# KiCad PCB

The board is a native KiCad 9 project composed from Python:

- `write_schematic.py` builds the native schematic and embedded symbol library.
- `generate.py` is the thin orchestration entry point for the eight-layer board.
- `core/kicad.py` provides the `KiCadBoard` object that owns native nets, pads,
  package attachment, manufacturing rules, traces, and vias.
- `core/connectivity.py` provides the validated object graph shared by PCB,
  schematic, and semantic component models.
- `core/board_builder.py` owns mechanical geometry and serialization;
  `core/routing.py` orders focused LED, control, sensor, and power routers from
  the neighbouring `routing_*.py` modules.
- `core/square.py` defines and validates one four-part square assembly—LED, Hall
  sensor, and both bypass capacitors—before placement repeats it 64 times.
- `design/netlist.json` is the reviewed connectivity contract; every placed
  component references an approved `part_key`. `design/project-template.json`
  is the reviewed seed from which the generated KiCad project settings are built.
- `generated/bom.md` is generated with exact manufacturer part numbers from
  `hardware/shared/components.py`; anonymous substitutions are rejected.
- `core/placement.py` composes square assemblies and one-off parts. Each
  `Placement` attaches itself through `KiCadBoard`; `footprints/` owns package
  geometry, while components resolve their semantic pin attachments through the
  shared connection graph.
- `hardware/shared/` supplies dimensions, component identities, and wiring.
- `generated/chess-board.kicad_pro`, `generated/chess-board.kicad_sch`, and
  `generated/chess-board.kicad_pcb` open directly in KiCad. All generated
  project, fabrication, report, render, BOM, and placement files live under
  `generated/`; the PCB root contains source code and reviewed design inputs only.

## Container operations

The PCB-local `Makefile` is the supported entry point from a host machine. Every
board operation executes in the reproducible KiCad 9 development container, so
host Python or KiCad versions cannot silently change the output:

```sh
make -C hardware/pcb help             # list all operations
make -C hardware/pcb test             # fast composition tests
make -C hardware/pcb component-check  # exact products, semantic pins, footprints
make -C hardware/pcb board            # regenerate native sources
make -C hardware/pcb review           # generation + ERC/DRC/parity/renders, no Gerbers
make -C hardware/pcb release          # gated fabrication export
make -C hardware/pcb shell            # container shell
make -C hardware/pcb down             # remove the container
```

`make release` runs `./tools/pcb`; it is not a shortcut around the release gate.
Manufacturing requirements are executable tests in
`tests/test_manufacturing_readiness.py`; release-only physical-evidence tests run
with `PCB_RELEASE=1` immediately before fabrication export.

## Product reality and readiness

Every fitted electrical part resolves to an explicit manufacturer and part
number in `hardware/shared/components.py`. The component-model tests require
that each product has a semantic pin enum and that its logical pins exactly
match its footprint. The generated BOM therefore contains purchasable product
identities rather than anonymous `R`, `C`, or connector placeholders.

That does **not** make the board automatically production-ready. Availability,
manufacturer drawing review, stack-up review, component 3D models, and physical
Hall-sensor/magnet validation remain real engineering gates. The repository currently
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
- Hall-sensor/magnet prototype evidence exists in `prototype/`.

The release-only unittest suite enforces the policy after review images are
created and before fabrication export. A failed test is a failed build, not a
warning.
