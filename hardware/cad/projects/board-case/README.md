# Board case

`generate.py` owns only `Printable_Board_Case` and its inspection render. Other
projects import `generated/board-case.blend`; they do not redefine this geometry.

344 x 384 x 30 mm, one piece, an open tub. The 40 mm of depth beyond the playing
area is the control strip, which is why the case is deeper than it is wide.

## What it holds

- **One PCB**, 320 x 360 mm, dropped into a pocket 0.5 mm larger per side. A
  ledge 2.5 mm under its edge carries the perimeter; the PCB keeps its bottom
  side clear for `PCB_BOTTOM_EDGE_KEEPOUT_MM` from the edge for it. Inside that,
  20 bosses stand on the grid lines.
  A panel that size flexes badly on perimeter support alone. The bosses are
  7 mm across because a grid line passes 7 mm from every LED position.
- **A Raspberry Pi Zero 2 W**, hanging component side up under the board on
  its header in the 18.4 mm cavity, at the shared Pi transform J1 is placed
  from. Its microSD end faces a slot in the right wall, pocketed from inside
  to 2 mm, and floor vents run under it.
- **The tile plate**, which also carries the control bezel, in a 3 mm rebate
  over the whole board, resting on a 7 mm rim outboard of the PCB pocket. The
  plate's eight screws land in that rim; anywhere further inboard is over the
  PCB.

Power enters through the back wall, below the board: a Switchcraft 722A panel jack at
x -141 and the RA11131100 snap-in rocker at x -20, both wired by a harness to
J4 on the board's underside. The wall is pocketed from inside down to each
part's panel thickness: 2.0 mm for the Switchcraft 722A (panels up to 0.125 in
per Switchcraft plf6) and 1.5 mm for the rocker, inside the 1.25-2.00 mm row of
the E-Switch RA1 sheet, whose 19.4 x 13.0 mm cutout the opening follows plus a
print allowance. The bay volumes behind both parts are bottom-side
PCB keepouts.

## Geometry is in assembly coordinates

The floor sits at z = 0 and the top face at `CASE_HEIGHT_MM`, so
`board-assembly` loads this part and the plate without moving either. Every
dimension comes from `core/dimensions.py`; nothing is hard-coded here except
where a feature sits along the wall it pierces.

Run `just --justfile hardware/cad/justfile generate` from the repository root.
