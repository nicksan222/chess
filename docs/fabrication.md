# PCB fabrication outputs

Run the single generator inside the devcontainer:

```sh
just --justfile hardware/pcb/justfile generate
```

It writes everything under `hardware/pcb/generated/`: the KiCad project,
schematics, BOM, component positions, previews, native check reports, and
`chess-board-fabrication.zip`. The ZIP contains RS-274X Gerbers for every copper
layer, both solder masks and silkscreens, the board outline and paste layers,
plus separate plated and non-plated Excellon drill files. Gerber and drill
coordinates use the same absolute origin. A layer-order note and drill report
are included. BOM and placement CSV remain beside the archive for assembly review.

The generator fills copper zones and requires zero native DRC violations,
unconnected pads and schematic parity mismatches, and runs the board-specific
SPICE tests before exporting fabrication
files. It checks that every expected layer and drill file is present and complete
before replacing the previous generated output.

These exports follow [PCBWay's KiCad fabrication-file guide](https://www.pcbway.com/helpcenter/generate_gerber/How_to_Export_Gerber__BOM__and_Pick_and_Place_Files_in_KiCad_9_0.html).

Manufacturing approval remains pending: electrical pin-role ERC, simulations
beyond the modeled sensing and button paths, stackup/manufacturing reassessment and the retained
[engineering assumptions](pcb-assumptions.md) still need review. `manifest.json`
records this status. The `release` command continues to refuse approval.

The board definition owns its layout and design rules. Components own narrow
package escapes and scoped local clearances. The harness renders the matching
KiCad rules and restricts narrow copper to each package's courtyard margin.

## PCBWay handoff

For **bare-board fabrication**, upload `chess-board-fabrication.zip` as a single
Gerber/drill archive. The outline defines a 320 × 380 mm board, 8 copper layers,
1.6 mm thickness, with copper order F.Cu, In1.Cu through In6.Cu, then B.Cu.
Use the outline's contour, not the Gerber-job bounding box including stroke width.
The drill report lists 870 plated holes (including 774 through vias) and 20
non-plated 3.4 mm mounting holes. The smallest actual plated drill is 0.4 mm.
Nominal routing is 0.31 mm width / 0.30 mm clearance; package escapes require
0.20 mm width / 0.16 mm clearance. Have PCBWay review these fine-pitch areas.

The archive contains every copper layer, front/back mask and silkscreen, outline,
paste, separate PTH/NPTH drills and a Gerber job with layer mappings. No native
KiCad files are needed to interpret that CAM set. Inspect all layers together in
`gerbview` or `gerbv` before uploading and check PCBWay's parsed layer order and
plated/non-plated holes before paying.

Ordering still requires choosing quantity, material/Tg, copper weights, solder
mask and silkscreen colors, surface finish and via treatment. Those production
choices and the exact dielectric stackup are **not approved by this refactor**;
the Gerber job's `Finish: None` is an unset field, not a request for bare copper.
The retained electrical calculations assume 1 oz copper and a PCBWay 8-layer
stackup; confirm those assumptions with the fabricator before fabrication.

For assembly review, use `hardware/pcb/generated/assembly-bom.csv` with
`assembly-smd.csv`; through-hole/hybrid placements are separated in
`assembly-through-hole.csv`. Raw `bom.csv` and enriched `positions.csv` remain
available for engineering review. The generated `assembly.md` records the native
KiCad coordinate conventions. Confirm origin, bottom-side rotation and polarized
pin orientation with the assembler before ordering. Harnesses are listed
separately in `harness.md` and `harness-bom.csv`.
