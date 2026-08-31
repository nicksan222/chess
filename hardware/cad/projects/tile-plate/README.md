# Tile plate

`generate.py` owns only `Printable_Tile_Plate` and its inspection render. Other
projects import `generated/tile-plate.blend`; they do not redefine this geometry.

319.6 x 319.6 x 3 mm, one print. Revision A needed 128 tile prints to cover the
board — 64 lids and 64 trays. This is the part that replaced all of them.

## Features

- **64 LED pockets** on the underside at the `LED_POSITION_MM` offset, leaving a
  1.2 mm skin that diffuses the light. The skin is that thick specifically so a
  dark-square recess cut into the top still leaves two nozzle widths above the
  pocket.
- **An engraved grid**: seven lines each way, 0.8 mm wide because a narrower
  slot will not resolve when printed.
- **32 recessed dark squares**, 0.4 mm deep, for paint or a filament change at
  that layer height.
- **64 underside pockets** on the 40 mm grid, leaving ribs on the grid lines.
  These do two jobs: a 3 mm solid sheet this size is a lot of material to have
  quoted and a warping risk, and the pockets are also the clearance over the
  reed switches and their solder joints.
- **Eight screws** with recessed heads, all landing on the case ledge. Nothing
  further inboard is possible, because the PCB is there.
- **A clipped A1 corner** so the plate cannot be fitted the wrong way round.

## Geometry is in assembly coordinates

The plate occupies the top 3 mm of the case, so `board-assembly` loads it and
the case without moving either. Every dimension comes from
`core/dimensions.py`.

Run `./tools/cad` from the repository root.
