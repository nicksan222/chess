# Tile plate

`generate.py` owns only `Printable_Tile_Plate` and its inspection render. Other
projects import `generated/tile-plate.blend`; they do not redefine this geometry.

335 x 375 x 3 mm, one print, covering the whole board. Revision A needed 128 tile prints to cover the
board — 64 lids and 64 trays. This is the part that replaced all of them.

## Features

- **64 LED pockets** on the underside at the `LED_POSITION_MM` offset, leaving a
  1.2 mm skin that diffuses the light. The skin is that thick specifically so a
  dark-square recess cut into the top still leaves two nozzle widths above the
  pocket.
- **An engraved grid**: nine lines each way, outline included, 0.8 mm wide
  because a narrower slot will not resolve when printed.
- **32 recessed dark squares**, 0.4 mm deep, for paint or a filament change at
  that layer height.
- **64 underside pockets** on the 40 mm grid, leaving ribs on the grid lines.
  These do two jobs: a 3 mm solid sheet this size is a lot of material to have
  quoted and a warping risk, and the pockets are also the clearance over the
  Hall sensors and their bypass capacitors.
- **Eight screws** with recessed heads, all landing on the case rim. Nothing
  further inboard is possible, because the PCB is there.
- **The control bezel** over the strip: twelve 5 mm button holes, each over a
  1 mm underside relief for the switch housing, and the display window inside
  the recess that holds the module. The bezel also keys the plate's
  orientation: rotated, the button stems stop it seating.

## Geometry is in assembly coordinates

The plate occupies the top 3 mm of the case, so `board-assembly` loads it and
the case without moving either. Every dimension comes from
`core/dimensions.py`.

Run `just --justfile hardware/cad/justfile generate` from the repository root.
