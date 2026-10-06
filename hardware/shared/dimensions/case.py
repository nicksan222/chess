"""Case envelope, vertical stack, Pi bay, and PCB supports.

Role: the open-tub case's measurements, derived from the board and plate sizes so a
change upstream propagates. Everything is in millimetres in board coordinates (origin
at the playing-area centre, Y up, +Y toward the rear wall) with Z measured from the
outside of the case floor. `validation.py` checks that the pieces fit each other;
`hardware/cad` generates the case from these values and `hardware/pcb` takes the Pi
header transform and the bottom-side keep-outs from here. Values marked UNVERIFIED are
also listed in `unverified.py`, which blocks PCB release until each is cleared.
"""

from .board import (
    PANEL_STRIP_DEPTH_MM,
    PCB_CENTER_OFFSET_Y_MM,
    PCB_SIZE_MM,
    PCB_THICKNESS_MM,
    PLAYING_SPAN_MM,
)
from .tile_plate import (
    TILE_PLATE_CLEARANCE_MM,
    TILE_PLATE_SIZE_MM,
    TILE_PLATE_THICKNESS_MM,
)

# --- Case -------------------------------------------------------------------
# The case is an open tub. The PCB drops straight into a pocket and rests on a
# ledge under its edge; the plate, which also carries the control bezel, closes
# the top. 12 mm leaves a solid wall outboard of the plate rebate.
CASE_FRAME_WIDTH_MM = 12.0
CASE_WALL_MM = 3.0
CASE_FLOOR_MM = 3.0
CASE_HEIGHT_MM = 30.0
CASE_OUTER_RADIUS_MM = 2.2
CASE_WIDTH_MM = PLAYING_SPAN_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_DEPTH_MM = PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_CENTER_OFFSET_Y_MM = PCB_CENTER_OFFSET_Y_MM
CASE_OUTER_SIZE_MM = (CASE_WIDTH_MM, CASE_DEPTH_MM, CASE_HEIGHT_MM)

# Vertical stack, measured from the outside of the case floor.
PCB_TO_PLATE_GAP_MM = 4.0
PCB_TOP_Z_MM = CASE_HEIGHT_MM - TILE_PLATE_THICKNESS_MM - PCB_TO_PLATE_GAP_MM
PCB_UNDERSIDE_Z_MM = PCB_TOP_Z_MM - PCB_THICKNESS_MM
PI_BAY_HEIGHT_MM = PCB_UNDERSIDE_Z_MM - CASE_FLOOR_MM

# A 320 mm board flexes badly on perimeter support alone, so bosses stand on the
# grid lines, where no LED or Hall sensor sits. Seven millimetres clears both.
PCB_SUPPORT_BOSS_DIAMETER_MM = 7.0
PCB_SUPPORT_PILOT_DIAMETER_MM = 2.5
PCB_MOUNTING_HOLE_DIAMETER_MM = 3.4
PCB_SUPPORT_PILOT_DEPTH_MM = 6.0
PCB_SUPPORT_GRID_OFFSETS_MM = (-120.0, -40.0, 40.0, 120.0)
PCB_SUPPORT_POSITIONS_MM = tuple(
    (x, y) for y in PCB_SUPPORT_GRID_OFFSETS_MM for x in PCB_SUPPORT_GRID_OFFSETS_MM
) + tuple(
    (x, -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0)
    for x in PCB_SUPPORT_GRID_OFFSETS_MM
)

# Raspberry Pi Zero 2 W hangs under the board on its header.
PI_BOARD_SIZE_MM = (65.0, 30.0, 1.4)
PI_HEADER_HEIGHT_MM = 8.5
PI_HEADER_BODY_MM = (51.0, 5.0, PI_HEADER_HEIGHT_MM)
PI_HEADER_ROTATION_DEG = 90.0
PI_CLEARANCE_MM = 2.0
PI_BAY_CENTER_MM = (0.0, -PLAYING_SPAN_MM / 2.0 + 40.0)
CASE_SD_SLOT_MM = (14.0, 3.5)
CASE_VENT_SLOT_MM = (40.0, 3.0)

# Rear wall apertures for the power input.
CASE_JACK_APERTURE_DIAMETER_MM = 8.0
CASE_ROCKER_APERTURE_MM = (19.0, 13.0)
CASE_REAR_APERTURE_CENTER_Z_MM = CASE_FLOOR_MM + PI_BAY_HEIGHT_MM / 2.0
