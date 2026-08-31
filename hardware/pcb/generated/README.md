# Generated KiCad review and fabrication output

`./tools/pcb` always writes review artifacts:

- `schematic/chess-board.svg` — complete native-schematic review drawing.
- `board-top.svg` and `board-bottom.svg` — board-fitted, full-color layer plots.
- `board-top.png` and `board-bottom.png` — orthographic 3D board renders.
- `board-3d.png` — high-quality perspective render with lighting and shadows.
- `erc.json`, `drc.rpt`, and `drc.json` — schematic, layout, and parity results.
- `audit.json` — BOM, MPN, schematic, DRC, connectivity, and prototype status.

Gerber and drill files are generated only after the release gate proves there
are no DRC exclusions, violations, parity errors, or unconnected items. If the
`gerber/` directory is absent, the design is intentionally not fabricable yet.

Do not edit generated artifacts.
