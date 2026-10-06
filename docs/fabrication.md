# PCB fabrication

The PCB is a native KiCad 9 project at `hardware/pcb/generated/chess-board.kicad_pro`.
Python composes the board through KiCad's `pcbnew` API, using shared dimensions,
wiring, reviewed connectivity, package geometry, and placement.

Run:

```sh
just --justfile hardware/pcb/justfile release
```

The runner regenerates the board, runs ERC, DRC with schematic parity and the test
suite (including SPICE), and only then exports Gerber files and separate plated and
non-plated Excellon drills under `hardware/pcb/generated`, next to the previews and
the generated BOM and harness table.

## Release gate

A fabrication package is acceptable only when `generated/drc.rpt` contains zero
violations and zero unconnected items, ERC and schematic parity are clean, and the
tests pass; `review` checks all of that. `release` adds two gates that refuse
together: the documented Hall-sensor/magnet prototype evidence
(`build.physical_evidence()`), and an empty `ASSUMPTIONS` list in
`hardware/pcb/definition/verification.py` (design values the datasheets do not give,
plus mechanical dimensions not yet measured). No Gerbers are written while either is
open, so `release` is expected to refuse until that work is done.

The build also writes `chess-board.kicad_dru`, a custom DRC rule that relaxes
clearance to 0.15 / 0.20 mm only for the fine-pitch eFuse (U74) and the copper at its
courtyard; every other item uses the board-wide 0.30 mm rules. The fabricator's ability
to assemble that QFN and to selectively solder the bottom-side through-hole parts is
still to be confirmed with them.

A clean DRC, a passing test suite and a render do not prove the board is safe or
manufacturable; they check the design files. See the
[PCB README](../hardware/pcb/README.md#verification-layers) for what is and is not
covered.

Before ordering, inspect the project in KiCad, clear the `ASSUMPTIONS` entries with a
datasheet or a measurement (land patterns are already checked against cited
datasheet rows), record the prototype evidence, run the PCB `release` recipe, and
inspect the board manufacturer's preview.
