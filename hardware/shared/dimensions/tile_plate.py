"""Printable tile-plate thickness, pockets, grooves, and fixings.

Role: the plate's own measurements, all derived from the PCB size so it always covers the
board with a fixed overhang. `case.py` sizes the plate rebate from it, and
`hardware/cad/projects/tile-plate` generates the part from these constants. Every feature
size is chosen for FDM printing (nozzle widths, minimum walls), not for appearance.
"""

from .board import PCB_CENTER_OFFSET_Y_MM, PCB_SIZE_MM, SQUARE_SIZE_MM

# Plate thickness. The case stack is built so the plate occupies the top 3 mm of the case.
TILE_PLATE_THICKNESS_MM = 3.0

# --- Tile plate -------------------------------------------------------------
# One flat overlay covering the whole board: the checkerboard engraved over the
# playing area and the control bezel over the strip. It overhangs the PCB so its
# edge rests on the case rim outboard of the board pocket, and the PCB can drop
# into the case before the plate goes on.
TILE_PLATE_CLEARANCE_MM = 0.4
TILE_PLATE_PCB_OVERHANG_MM = 7.5
TILE_PLATE_SIZE_MM = (
    PCB_SIZE_MM[0] + 2.0 * TILE_PLATE_PCB_OVERHANG_MM,
    PCB_SIZE_MM[1] + 2.0 * TILE_PLATE_PCB_OVERHANG_MM,
    TILE_PLATE_THICKNESS_MM,
)
TILE_PLATE_CENTER_Y_MM = PCB_CENTER_OFFSET_Y_MM
# The rebate is as deep as the plate is thick, so the plate sits flush with the rim.
TILE_PLATE_REBATE_DEPTH_MM = TILE_PLATE_THICKNESS_MM
# Thick enough that a dark-square recess cut into the top still leaves two
# nozzle widths of material over the LED pocket below.
TILE_PLATE_DIFFUSER_SKIN_MM = 1.2
# LED pocket footprint and depth: the depth leaves the diffuser skin above it.
TILE_PLATE_LED_POCKET_MM = (
    6.2,
    6.2,
    TILE_PLATE_THICKNESS_MM - TILE_PLATE_DIFFUSER_SKIN_MM,
)
# Two nozzle widths: a narrower slot will not resolve when printed.
TILE_PLATE_GROOVE_WIDTH_MM = 0.8
TILE_PLATE_GROOVE_DEPTH_MM = 0.6
TILE_PLATE_DARK_SQUARE_DEPTH_MM = 0.4
# One pocket per square on the underside, leaving ribs on the grid lines. It
# does two jobs: it removes most of a 320 mm solid sheet's volume, which is a
# real line on a print-service quote and a warping risk, and it is also the
# clearance over the Hall sensors and nearby bypass capacitors.
TILE_PLATE_RIB_WIDTH_MM = 3.0
TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM = 1.2
TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM = SQUARE_SIZE_MM - 2.0 * TILE_PLATE_RIB_WIDTH_MM
# Eight screws (see positions below): the through hole, its recessed head and the inset
# from the plate edge, which keeps the screw over the case rim rather than the PCB.
TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM = 3.4
TILE_PLATE_SCREW_HEAD_DIAMETER_MM = 6.4
TILE_PLATE_SCREW_HEAD_DEPTH_MM = 1.6
TILE_PLATE_SCREW_INSET_MM = 4.0
_SCREW_X_MM = TILE_PLATE_SIZE_MM[0] / 2.0 - TILE_PLATE_SCREW_INSET_MM
_SCREW_Y_MM = TILE_PLATE_SIZE_MM[1] / 2.0 - TILE_PLATE_SCREW_INSET_MM
# Four corners and four edge midpoints: every one lands on the case rim.
TILE_PLATE_SCREW_POSITIONS_MM = tuple(
    (x, TILE_PLATE_CENTER_Y_MM + y)
    for x, y in (
        (-_SCREW_X_MM, -_SCREW_Y_MM),
        (0.0, -_SCREW_Y_MM),
        (_SCREW_X_MM, -_SCREW_Y_MM),
        (-_SCREW_X_MM, 0.0),
        (_SCREW_X_MM, 0.0),
        (-_SCREW_X_MM, _SCREW_Y_MM),
        (0.0, _SCREW_Y_MM),
        (_SCREW_X_MM, _SCREW_Y_MM),
    )
)
