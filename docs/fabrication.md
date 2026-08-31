# PCB fabrication

The PCB is a native KiCad 9 project at `hardware/pcb/chess-board.kicad_pro`.
Python composes the board through KiCad's `pcbnew` API, using shared dimensions,
wiring, reviewed connectivity, package geometry, and placement.

Run:

```sh
./tools/pcb
```

The runner regenerates the board, executes KiCad DRC, and exports Gerber,
Excellon, and preview files under `hardware/pcb/generated`.

## Release gate

A fabrication package is acceptable only when `generated/drc.rpt` contains zero
violations and zero unconnected items. The current migration preserves placement
and connectivity but deliberately discards unsafe custom routing, so it is not
yet ready to order.

Before ordering, inspect the project in KiCad, verify footprints against vendor
datasheets, complete routing and copper zones in generator-owned code, run DRC,
and inspect the board manufacturer's preview.
