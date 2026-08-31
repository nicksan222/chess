# Board assembly

Presentation only. This project owns no printable geometry: it opens
`generated/board-case.blend`, imports `Printable_Tile_Plate` exactly as
`tile-plate` produced it, and adds a non-printed proxy for the populated circuit
board from `blocks/pcb_proxy.py`.

Published output is `board-assembly-finished.png` and `board-assembly-open.png`.

## Nothing is positioned here

Both printable parts are generated in assembly coordinates: the case floor sits
at z = 0 and the plate occupies the top 3 mm. So this file moves neither of them.
That is deliberate. If the plate ever stops meeting the case, it is a real error
in `core/dimensions.py` rather than a positioning mistake in a view, and the
render will show it.

The open view is the exception: it lifts the plate clear of the case so the
board, the expanders and the Pi underneath are visible.

## The board proxy is not authoritative

`hardware/electronics` owns the circuit design. The proxy exists so the assembly
render shows what fills the cavity, and so the vertical stack in
`core/dimensions.py` can be seen to add up rather than only asserted. Its
positions are derived from the shared dimensions, so it follows any change to
the square pitch or the board thickness.

Run `./tools/cad` from the repository root.
