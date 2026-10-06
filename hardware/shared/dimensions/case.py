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
PCB_POCKET_CLEARANCE_MM = 0.5
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

# Raspberry Pi Zero 2 W hangs component side up under the board, its male
# header plugged up into J1 on the PCB bottom. Seen from the PCB top it is the
# RP-008358-DS-1 drawing view, rotated but never mirrored. Drawing frame: origin
# at the Pi's bottom-left corner, header along the top edge, microSD at the left.
PI_BOARD_SIZE_MM = (65.0, 30.0, 1.4)
# Header centre: left hole (3.5) + 29 along X, on the hole line 3.5 below the top.
PI_HEADER_ON_PI_MM = (32.5, PI_BOARD_SIZE_MM[1] - 3.5)
PI_HEADER_PITCH_MM = 2.54
PI_HEADER_PIN_COUNT = 40
# Board placement: the header centre is the one anchor; everything else derives.
PI_HEADER_CENTER_MM = (123.0, -75.0)
PI_ROTATION_DEG = 180.0
# Stack: Sullins PPPC202LFBN-RC insulator .334 in (8.50) on the PCB plus the
# PRPC020DAAN-RC insulator .100 in (2.54) on the Pi.
PI_HEADER_HEIGHT_MM = 8.5
PI_MALE_HEADER_INSULATOR_MM = 2.54
PI_BOARD_TO_BOARD_MM = PI_HEADER_HEIGHT_MM + PI_MALE_HEADER_INSULATOR_MM
PI_HEADER_BODY_MM = (51.0, 5.0, PI_HEADER_HEIGHT_MM)
PI_CLEARANCE_MM = 2.0

# The Pi is only ever placed at multiples of 90 degrees, so rotation is done exactly
# with these cos/sin pairs instead of floating-point trigonometry.
_QUARTER_TURNS = {0: (1.0, 0.0), 90: (0.0, 1.0), 180: (-1.0, 0.0), 270: (0.0, -1.0)}


def _rotate(vector: tuple[float, float], degrees: float) -> tuple[float, float]:
    """Exact rotation by a quarter turn, which is all a placement here uses."""
    cos, sin = _QUARTER_TURNS[int(degrees) % 360]
    return (vector[0] * cos - vector[1] * sin, vector[0] * sin + vector[1] * cos)


def pi_on_board_xy(point_on_pi: tuple[float, float]) -> tuple[float, float]:
    """Board XY, seen from the PCB top, of a point in the Pi drawing frame."""
    dx, dy = _rotate(
        (
            point_on_pi[0] - PI_HEADER_ON_PI_MM[0],
            point_on_pi[1] - PI_HEADER_ON_PI_MM[1],
        ),
        PI_ROTATION_DEG,
    )
    return (PI_HEADER_CENTER_MM[0] + dx, PI_HEADER_CENTER_MM[1] + dy)


def pi_header_pin_xy(pin: int) -> tuple[float, float]:
    """Board XY, seen from the PCB top, of Pi GPIO header pin 1..40.

    Pin 1 is the square pad at the microSD end of the inner row; odd pins run
    along the inner row and even pins along the outer row, at the board edge.
    """
    if not 1 <= pin <= PI_HEADER_PIN_COUNT:
        raise ValueError(f"Pi header pin {pin} is outside 1..{PI_HEADER_PIN_COUNT}")
    column = (pin - 1) // 2
    half_rows = PI_HEADER_PITCH_MM / 2.0
    return pi_on_board_xy(
        (
            PI_HEADER_ON_PI_MM[0] + (column - 9.5) * PI_HEADER_PITCH_MM,
            PI_HEADER_ON_PI_MM[1] + (half_rows if pin % 2 == 0 else -half_rows),
        )
    )


# Rear wall apertures for the power input.
CASE_JACK_APERTURE_DIAMETER_MM = 8.0
CASE_ROCKER_APERTURE_MM = (19.0, 13.0)
CASE_REAR_APERTURE_CENTER_Z_MM = CASE_FLOOR_MM + PI_BAY_HEIGHT_MM / 2.0
