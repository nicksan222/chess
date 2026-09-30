"""Printable tile-plate thickness, pockets, grooves, and fixings."""

from .board import PLAYING_SPAN_MM, SQUARE_SIZE_MM

TILE_PLATE_THICKNESS_MM = 3.0

# --- Tile plate -------------------------------------------------------------
# One flat overlay with the checkerboard engraved into it, sitting in a rebate
# over the playing area. The control strip is not covered; it shows through the
# case bezel.
TILE_PLATE_CLEARANCE_MM = 0.4
TILE_PLATE_SPAN_MM = PLAYING_SPAN_MM - TILE_PLATE_CLEARANCE_MM
TILE_PLATE_SIZE_MM = (
    TILE_PLATE_SPAN_MM,
    TILE_PLATE_SPAN_MM,
    TILE_PLATE_THICKNESS_MM,
)
TILE_PLATE_REBATE_DEPTH_MM = TILE_PLATE_THICKNESS_MM
# Thick enough that a dark-square recess cut into the top still leaves two
# nozzle widths of material over the LED pocket below.
TILE_PLATE_DIFFUSER_SKIN_MM = 1.2
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
TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM = 3.4
TILE_PLATE_SCREW_HEAD_DIAMETER_MM = 6.4
TILE_PLATE_SCREW_HEAD_DEPTH_MM = 1.6
TILE_PLATE_SCREW_INSET_MM = 4.0
_PLATE_SCREW_OFFSET_MM = TILE_PLATE_SPAN_MM / 2.0 - TILE_PLATE_SCREW_INSET_MM
# Four corners and four edge midpoints: every one lands on the case ledge.
TILE_PLATE_SCREW_POSITIONS_MM = (
    (-_PLATE_SCREW_OFFSET_MM, -_PLATE_SCREW_OFFSET_MM),
    (0.0, -_PLATE_SCREW_OFFSET_MM),
    (_PLATE_SCREW_OFFSET_MM, -_PLATE_SCREW_OFFSET_MM),
    (-_PLATE_SCREW_OFFSET_MM, 0.0),
    (_PLATE_SCREW_OFFSET_MM, 0.0),
    (-_PLATE_SCREW_OFFSET_MM, _PLATE_SCREW_OFFSET_MM),
    (0.0, _PLATE_SCREW_OFFSET_MM),
    (_PLATE_SCREW_OFFSET_MM, _PLATE_SCREW_OFFSET_MM),
)
TILE_PLATE_ORIENTATION_NOTCH_MM = (6.0, 6.0, TILE_PLATE_THICKNESS_MM)
