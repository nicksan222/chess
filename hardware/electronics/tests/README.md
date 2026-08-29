# Electronics tests

This directory verifies schematic ownership, reusable cells, and Schemdraw
topology. Tests run through `./tools/electronics`, which installs the
toolchain if needed, runs these tests, then generates SVG and PNG drawings.

Generator-structure tests check `generation-order` so the square and chessboard
projects run in dependency order. They ensure every schematic has
one owning generator, that `components/` stays a catalog of single parts rather
than compositions, and that shared modules do not drift back into the root.

The repository quality gate discovers these tests automatically through
`make check`.
