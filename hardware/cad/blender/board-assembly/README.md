# Printable board assembly views

This directory owns presentation-only compositions of the empty printable board
and the separately printed universal tiles.

`loading.png` shows three installed rows, the exposed Velcro/screw mounting floor,
and one tile hovering above its position. `finished.png` shows all 64 tile lids
forming the checkerboard. The source board in `board-skeleton` remains empty.

The generator imports the exact generated tile lid and tray meshes; it does not
redefine printable parts. Run `make regen-all` from the repository root to
regenerate both views.
