# Electronics tests

This directory verifies schematic ownership, reusable cells, and Schemdraw
topology. Tests run through `./tools/electronics check`, which also generates
SVG and PNG drawings.

Generator-structure tests require the electronics runner to discover the square
and chessboard projects in dependency order. They ensure every schematic has
one owning generator, that `components/` stays a catalog of single parts rather
than compositions, and that shared modules do not drift back into the root.

The repository quality gate discovers these tests automatically through
`make check`.
