# Generated KiCad review and fabrication output

`./tools/pcb` keeps every generated artifact in this directory. Apart from this
README, its contents are disposable and reproducible from the PCB source and
`design/` inputs:

- `chess-board.kicad_pro`, `chess-board.kicad_sch`, and
  `chess-board.kicad_pcb` — the complete native KiCad project.
- `generated-symbols.kicad_sym` and `sym-lib-table` — project-local generated
  symbol library configuration.
- `schematic/chess-board.svg` — complete native-schematic review drawing.
- `board-top.svg` and `board-bottom.svg` — board-fitted, full-color layer plots.
- `board-top.png` and `board-bottom.png` — orthographic 3D board renders.
- `board-3d.png` — high-quality perspective render with lighting and shadows.
- `erc.json`, `drc.rpt`, and `drc.json` — schematic, layout, and parity results.
- `assembly-bom.csv` and `positions.csv` — PCBWay-compatible fitted-parts BOM
  and component placement list; external modules and the PSU remain in
  `bom.md` only.

Gerber and drill files are generated only after the release gate proves there
are no DRC exclusions, violations, parity errors, or unconnected items. If the
`gerber/` directory is absent, the design is intentionally not fabricable yet.

Do not edit generated artifacts.
