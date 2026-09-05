# PCB fabrication

The PCB is a native KiCad 9 project at `hardware/pcb/generated/chess-board.kicad_pro`.
Python composes the board through KiCad's `pcbnew` API, using shared dimensions,
wiring, reviewed connectivity, package geometry, and placement.

Run:

```sh
just --justfile hardware/pcb/justfile release
```

The runner regenerates the board, executes KiCad DRC, and exports Gerber,
Excellon, and preview files under `hardware/pcb/generated`.

## Release gate

A fabrication package is acceptable only when `generated/drc.rpt` contains zero
violations and zero unconnected items. Copper routing and zones now satisfy that
gate. Ordering remains blocked until native schematic parity and the documented
Hall-sensor/magnet prototype evidence also pass.

Before ordering, inspect the project in KiCad, verify footprints against vendor
datasheets, complete the remaining release evidence, run the PCB `release` recipe, and
inspect the board manufacturer's preview.
