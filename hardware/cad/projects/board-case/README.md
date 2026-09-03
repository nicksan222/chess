# Board case

`generate.py` owns only `Printable_Board_Case` and its inspection render. Other
projects import `generated/board-case.blend`; they do not redefine this geometry.

340 x 380 x 30 mm, one piece. The 40 mm of depth beyond the playing area is the
control strip, which is why the case is deeper than it is wide.

## What it holds

- **One PCB**, 320 x 360 mm, carried on 20 bosses standing on the grid lines.
  A panel that size flexes badly on perimeter support alone. The bosses are
  7 mm across because a grid line passes 7 mm from every LED position.
- **A Raspberry Pi Zero 2 W**, hanging under the board on its header in the
  18.4 mm cavity, with a card slot in the right wall and vents in the floor.
- **Twelve buttons and an OLED**, through a face-up bezel across the front
  strip. Facing up is what keeps every part on one side of the PCB and avoids
  right-angle components.
- **The tile plate**, in a 3 mm rebate over the playing area, resting on an 8 mm
  ledge. The plate's eight screws land in that ledge; anywhere further inboard
  is over the PCB.

Power enters through the back wall: a barrel jack and a rocker switch, both
positioned in the cavity below the board rather than behind the playing surface.

## Geometry is in assembly coordinates

The floor sits at z = 0 and the top face at `CASE_HEIGHT_MM`, so
`board-assembly` loads this part and the plate without moving either. Every
dimension comes from `core/dimensions.py`; nothing is hard-coded here except
where a feature sits along the wall it pierces.

Run `just --justfile hardware/cad/justfile generate` from the repository root.
