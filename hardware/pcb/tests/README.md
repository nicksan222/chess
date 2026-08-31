# PCB tests

These run without Gerbonara writing anything, so they are fast and they gate the
build:

- `test_rules.py` — the chosen geometry is inside the fab's stated capability,
  and raising a limit past it is refused rather than silently accepted.
- `test_footprints.py` — every package the design contract places has copper to land
  on, every design contract pin has a pad, and no two pads within a footprint collide.
- `test_placement.py` — nothing overlaps, nothing hangs off the board, and every
  LED, reed and button sits where the mechanical design already put a pocket or
  a hole.
- `test_fabrication.py` — the layer stack is complete, the ground pour clears
  every pad that is not on ground, the written Gerbers read back as what was
  meant, and the upload package does not exist while any net is unrouted.

The last one is the important one. There is no design-rule checker here, so
these tests are the whole guarantee, and they are worth exactly what they claim:
they confirm the geometry is manufacturable and the nets are joined. They do not
confirm that copper is clear of copper.
