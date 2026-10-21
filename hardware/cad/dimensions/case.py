"""Case envelope, vertical stack, Pi bay, and PCB supports.

Role: the open-tub case's measurements, derived from the board and plate sizes so a
change upstream propagates. Everything is in millimetres in board coordinates (origin
at the playing-area centre, Y up, +Y toward the rear wall) with Z measured from the
outside of the case floor. `validation.py` checks that the pieces fit each other and
the case is generated from these values. The board outline, the Pi placement and the
mounting holes come from the PCB export (`board.py`). Values marked UNVERIFIED are also
listed in `unverified.py` until each is cleared.
"""

from .board import (
    JACK,
    PANEL_STRIP_DEPTH_MM,
    PCB_CENTER_OFFSET_Y_MM,
    PCB_SIZE_MM,
    PCB_THICKNESS_MM,
    PI_BOARD_TO_BOARD_MM,
    PI_SD_SOCKET_HEIGHT_MM,
    PI_SD_SOCKET_MM,
    PLAYING_SPAN_MM,
    ROCKER,
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
# Product guard rail: the finished compact board, case included, stays this low.
COMPACT_BOARD_MAX_HEIGHT_MM = 35.0
PCB_POCKET_CLEARANCE_MM = 0.5
# The generated PCB has square edges; a 3D bevel here clips its bottom perimeter.
PCB_POCKET_RADIUS_MM = 0.0
PCB_POCKET_SIZE_MM = (
    PCB_SIZE_MM[0] + 2.0 * PCB_POCKET_CLEARANCE_MM,
    PCB_SIZE_MM[1] + 2.0 * PCB_POCKET_CLEARANCE_MM,
)
# How far the ledge reaches in under the nominally centred board edge.
CASE_PCB_LEDGE_OVERLAP_MM = 2.5
CASE_CAVITY_SIZE_MM = (
    PCB_SIZE_MM[0] - 2.0 * CASE_PCB_LEDGE_OVERLAP_MM,
    PCB_SIZE_MM[1] - 2.0 * CASE_PCB_LEDGE_OVERLAP_MM,
)
# The plate rests on a rim outboard of the PCB pocket and its screws land there.
CASE_PLATE_REBATE_MM = (
    TILE_PLATE_SIZE_MM[0] + TILE_PLATE_CLEARANCE_MM,
    TILE_PLATE_SIZE_MM[1] + TILE_PLATE_CLEARANCE_MM,
)
CASE_PLATE_LEDGE_MM = (TILE_PLATE_SIZE_MM[0] - PCB_POCKET_SIZE_MM[0]) / 2.0
CASE_OUTER_RADIUS_MM = 2.2
CASE_WIDTH_MM = PLAYING_SPAN_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_DEPTH_MM = PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_CENTER_OFFSET_Y_MM = PCB_CENTER_OFFSET_Y_MM
CASE_OUTER_SIZE_MM = (CASE_WIDTH_MM, CASE_DEPTH_MM, CASE_HEIGHT_MM)

# Vertical stack, measured from the outside of the case floor. The case height is
# fixed (CASE_HEIGHT_MM); the PCB height and the Pi bay are what is left after the plate
# and the PCB-to-plate gap, and `validate()` insists the pieces sum exactly.
PCB_TO_PLATE_GAP_MM = 4.0
PCB_TOP_Z_MM = CASE_HEIGHT_MM - TILE_PLATE_THICKNESS_MM - PCB_TO_PLATE_GAP_MM
PCB_UNDERSIDE_Z_MM = PCB_TOP_Z_MM - PCB_THICKNESS_MM
PI_BAY_HEIGHT_MM = PCB_UNDERSIDE_Z_MM - CASE_FLOOR_MM

# A 320 mm board flexes badly on perimeter support alone, so a boss stands under
# each PCB mounting hole (`PCB_SUPPORT_POSITIONS_MM`, from the export).
PCB_SUPPORT_BOSS_DIAMETER_MM = 7.0
PCB_SUPPORT_PILOT_DIAMETER_MM = 2.5
PCB_SUPPORT_PILOT_DEPTH_MM = 6.0

# The Pi hangs from J1 under the board; the PCB owns its placement and stack.
PI_CLEARANCE_MM = 2.0

# The Pi's floor vents run along its long axis, under it.
# Slot size (length along the Pi's long axis, width) of each floor vent.
CASE_VENT_SLOT_MM = (40.0, 3.0)
PI_TOP_FACE_Z_MM = PCB_UNDERSIDE_Z_MM - PI_BOARD_TO_BOARD_MM
# Wall slot size for the card: width along the wall, height.
CASE_SD_SLOT_MM = (14.0, 3.5)
CASE_SD_SLOT_CENTER_Y_MM = PI_SD_SOCKET_MM[1]
CASE_SD_SLOT_CENTER_Z_MM = PI_TOP_FACE_Z_MM + PI_SD_SOCKET_HEIGHT_MM / 2.0
# The right wall is pocketed from inside around the slot so a card standing
# proud of the Pi clears it and tweezers can reach the card edge.
CASE_SD_PANEL_THICKNESS_MM = 2.0
CASE_SD_POCKET_WIDTH_MM = CASE_SD_SLOT_MM[0] + 4.0

# Wall pockets below the PCB run from the floor up to a printable roof that
# keeps the PCB ledge continuous above them.
CASE_WALL_POCKET_ROOF_MM = 1.0
CASE_WALL_POCKET_Z_MM = (CASE_FLOOR_MM, PCB_UNDERSIDE_Z_MM - CASE_WALL_POCKET_ROOF_MM)

# Rear wall apertures for the panel-mounted power input, wired to J4.
CASE_REAR_APERTURE_CENTER_Z_MM = CASE_FLOOR_MM + PI_BAY_HEIGHT_MM / 2.0
# Switchcraft 722A (customer drawing 712A 722A 732A rev J, exported by the PCB):
# 5/16-32 NEF bushing threaded ahead of the flange that bears on the inside of the
# panel; washer and hex nut go on the outside. The wall is pocketed to 2.0.
CASE_JACK_BUSHING_DIAMETER_MM = JACK.bushing_diameter_mm
CASE_JACK_PRINT_ALLOWANCE_MM = 0.13
CASE_JACK_APERTURE_DIAMETER_MM = (
    CASE_JACK_BUSHING_DIAMETER_MM + 2.0 * CASE_JACK_PRINT_ALLOWANCE_MM
)
CASE_JACK_APERTURE_CENTER_X_MM = -141.0
CASE_JACK_THREAD_LENGTH_MM = JACK.thread_length_mm
CASE_JACK_MAX_PANEL_MM = JACK.max_panel_mm
CASE_JACK_PANEL_THICKNESS_MM = 2.0
CASE_JACK_FLANGE_DIAMETER_MM = JACK.flange_diameter_mm
# Clears the Ø11.0 flange and the solder lugs behind the panel.
CASE_JACK_POCKET_WIDTH_MM = 16.0
# 20.8 overall less the 5.46 thread leaves 15.3 behind the panel to the lug
# ends; the rest is room for the soldered wires.
CASE_JACK_BAY_DEPTH_MM = 30.0
# E-Switch RA11131100 snap-in rocker, RA1 series sheet (11.3.2022) p2, 2-position
# non-illuminated: recommended cutout 13.00 high and 19.4 wide for a 1.25-2.00 mm
# panel. A printed hole closes up, so each side gets a small allowance.
CASE_ROCKER_CUTOUT_MM = ROCKER.cutout_mm
CASE_ROCKER_PANEL_RANGE_MM = ROCKER.panel_range_mm
CASE_ROCKER_PRINT_ALLOWANCE_MM = 0.1
CASE_ROCKER_APERTURE_MM = (
    CASE_ROCKER_CUTOUT_MM[0] + 2.0 * CASE_ROCKER_PRINT_ALLOWANCE_MM,
    CASE_ROCKER_CUTOUT_MM[1] + 2.0 * CASE_ROCKER_PRINT_ALLOWANCE_MM,
)
CASE_ROCKER_APERTURE_CENTER_X_MM = -20.0
# Inside the sheet's 1.25-2.00 mm row, with print tolerance either way.
CASE_ROCKER_PANEL_THICKNESS_MM = 1.5
# The rear wall is pocketed from inside down to the panel thickness, with room
# around the cutout for the snap-in latches.
CASE_ROCKER_POCKET_MARGIN_MM = 2.5
CASE_ROCKER_LATCH_MARGIN_MM = 1.5
CASE_ROCKER_POCKET_ROOF_MM = CASE_WALL_POCKET_ROOF_MM
CASE_ROCKER_POCKET_WIDTH_MM = (
    CASE_ROCKER_APERTURE_MM[0] + 2.0 * CASE_ROCKER_POCKET_MARGIN_MM
)
CASE_ROCKER_POCKET_Z_MM = CASE_WALL_POCKET_Z_MM
# Rocker body and tabs reach 18.5 +/- 1.0 mm behind the panel (RA1 sheet p2);
# the rest is the two insulated FASTON receptacles and their wire exit.
CASE_ROCKER_BAY_DEPTH_MM = 50.5

# Bottom-side PCB keepouts in the bay (x0, x1, y0, y1): the panel parts and
# their wiring hang there, below the board. The PCB tests (`test_bottom_side.py`) keep
# bottom-side parts out of these rectangles; the Y extent runs from the rear wall's
# inner panel face forward by the part's bay depth.
_REAR_WALL_OUTER_Y_MM = CASE_CENTER_OFFSET_Y_MM + CASE_DEPTH_MM / 2.0
BOTTOM_SIDE_KEEPOUTS_MM = {
    "rocker": (
        CASE_ROCKER_APERTURE_CENTER_X_MM - CASE_ROCKER_POCKET_WIDTH_MM / 2.0,
        CASE_ROCKER_APERTURE_CENTER_X_MM + CASE_ROCKER_POCKET_WIDTH_MM / 2.0,
        _REAR_WALL_OUTER_Y_MM
        - CASE_ROCKER_PANEL_THICKNESS_MM
        - CASE_ROCKER_BAY_DEPTH_MM,
        _REAR_WALL_OUTER_Y_MM - CASE_ROCKER_PANEL_THICKNESS_MM,
    ),
    "jack": (
        CASE_JACK_APERTURE_CENTER_X_MM - CASE_JACK_POCKET_WIDTH_MM / 2.0,
        CASE_JACK_APERTURE_CENTER_X_MM + CASE_JACK_POCKET_WIDTH_MM / 2.0,
        _REAR_WALL_OUTER_Y_MM - CASE_JACK_PANEL_THICKNESS_MM - CASE_JACK_BAY_DEPTH_MM,
        _REAR_WALL_OUTER_Y_MM - CASE_JACK_PANEL_THICKNESS_MM,
    ),
}
