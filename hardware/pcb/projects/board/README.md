# Board layout

`generate.py` owns the board's artwork. One project, because there is one PCB.

Published output is in `hardware/pcb/generated`: the Gerber and Excellon stack in
`gerber/`, previews of both sides, `routing.md`, and `board-pcbway.zip` when and
only when the layout is complete.

## What is routed, and why only that

Stage one routes what the board's regularity makes unambiguous:

- **The LED chain**, all 126 links. Consecutive LEDs in the serpentine are always
  exactly one square pitch apart, and always either along a rank or straight up a
  file, so clock and data need no obstacle reasoning at all. Seven of the links
  are rank turns and take a right angle; the rest are single straight segments.
- **Ground.** Every through-hole pad on ground already reaches the bottom pour,
  so those need no trace. The 64 surface-mount LED ground pads get a stub and a
  via each.

What is left is the 64 reed sense lines, the I2C and SPI buses, the panel button
lines, and 5 V distribution. Those all compete for the same top-layer space and
need a router that reasons about obstacles.

Routing is driven by the published connection list rather than by rebuilding the
schematic's intent here. Routing what the schematic says, instead of what this
module believes it says, is what stops the two drifting apart.

## The ground pour is negative

A filled region on the bottom layer would short every through-hole pad on the
board to ground — the difference between a ground plane and a scrapped board. So
the pour is painted dark, clearances are painted in **clear** polarity to cut
holes around every pad not on ground, and ground pads are then repainted dark so
they stay attached. Order is significant, and `test_fabrication.py` asserts it.

## Placement comes from the mechanical design

Every LED sits where the tile plate has a diffuser pocket. Every reed sits at a
square centre. Every button sits under a bezel hole. Those positions are read
from `hardware/shared/dimensions.py`, so the copper and the plastic cannot
disagree.

The expanders are the exception worth knowing about: a PDIP-28 is nearly as long
as a square, and the quadrant centre it wants is taken by an LED, so each one
sits 14 mm to one side. The tests confirm no part overlaps another.

Run `./tools/pcb` from the repository root.
