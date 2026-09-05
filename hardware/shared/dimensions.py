"""Authoritative millimetre dimensions and physical guardrails for Chess CAD.

Revision B is two printed parts: a case that holds one PCB and the Raspberry Pi,
and a single tile plate that lays the checkerboard over the whole playing area.
The 64 individually printed two-part tiles of revision A are gone, and with them
every tile enclosure, wire port and Velcro pocket dimension.

Coordinates are centred on the playing area, not on the case. The control strip
extends in negative Y, so the case is offset by `CASE_CENTER_OFFSET_Y_MM` while
square centres, LED positions and Hall-sensor positions stay symmetric about
that origin.
"""

from math import ceil, isclose
from types import MappingProxyType

from .components import BUTTON, HALL_SENSOR, OLED_MODULE, SK9822, TCA9554
from .hall_banks import banks

# Unit contract. One Blender unit represents one millimetre in generated files.
MILLIMETRES_PER_METRE = 1_000.0
MILLIMETRES_PER_INCH = 25.4
BLENDER_SCALE_LENGTH = 1.0 / MILLIMETRES_PER_METRE

# Project form factor. This is a compact electronic board, not a FIDE-sized board.
BOARD_FORMAT = "compact electronic"
COMPACT_SQUARE_MIN_MM = 35.0
COMPACT_SQUARE_MAX_MM = 45.0
COMPACT_BOARD_MIN_SPAN_MM = 300.0
COMPACT_BOARD_MAX_SPAN_MM = 400.0
COMPACT_BOARD_MAX_HEIGHT_MM = 35.0
FIDE_REFERENCE_SQUARE_MIN_MM = 50.0
FIDE_REFERENCE_SQUARE_MAX_MM = 60.0

# Prototype FDM guardrails. These catch implausible geometry, but do not replace
# printer-, material-, and orientation-specific slicer validation.
#
# Both parts are larger than a desktop printer bed, so they are quoted from an
# FDM print service. The desktop figure is kept to document that fact rather than
# to gate anything: a 380 mm case does not fit a 256 mm bed and never will.
REFERENCE_DESKTOP_BUILD_VOLUME_MM = (256.0, 256.0, 256.0)
REFERENCE_SERVICE_BUILD_VOLUME_MM = (420.0, 420.0, 420.0)
PRINT_BED_EDGE_MARGIN_MM = 5.0
FDM_REFERENCE_NOZZLE_MM = 0.4
FDM_MIN_FEATURE_MM = 2.0 * FDM_REFERENCE_NOZZLE_MM
FDM_MIN_FLOOR_MM = 1.0
FDM_MIN_FIT_CLEARANCE_MM = 0.2
FDM_MAX_FIT_CLEARANCE_MM = 0.5

# Boolean robustness. Cutters overhang the surface they break so coplanar faces
# never meet, which is what keeps the exact solver from leaving holes.
BOOLEAN_RECESS_OVERLAP_MM = 0.2
BOOLEAN_THROUGH_OVERLAP_MM = 0.4

# Board grid. Unchanged from revision A: 40 mm squares suit a chess set with a
# king base of 32 mm or less, which covers most ordinary club sets.
GRID_COUNT = 8
SQUARE_SIZE_MM = 40.0
PLAYING_SPAN_MM = SQUARE_SIZE_MM * GRID_COUNT

# SK9822 5050 addressable RGB LED. Mechanically interchangeable with the
# WS2812B this design replaced, so the pocket dimensions are unchanged; the
# difference is electrical, a separate clock line the host can drive from SPI.
# https://www.ledyilighting.com/wp-content/uploads/2025/02/WS2812B-datasheet.pdf
LED_PACKAGE_REFERENCE = SK9822.description
LED_PACKAGE_NOMINAL_SIZE_MM = SK9822.require_body_mm()
LED_PACKAGE_TOLERANCE_MM = 0.05
LED_PACKAGE_MAX_SIZE_MM = tuple(
    axis + LED_PACKAGE_TOLERANCE_MM for axis in LED_PACKAGE_NOMINAL_SIZE_MM
)
LED_PACKAGE_CLEARANCE_PER_SIDE_MM = 0.2
LED_EMITTER_WINDOW_MM = (4.0, 4.0)
LED_POSITION_MM = (13.0, 13.0)

# SOT-23 omnipolar Hall sensor at each square centre. Either magnet pole drives
# its active-low output, preserving the old occupied-square electrical polarity.
HALL_SENSOR_PACKAGE_MM = HALL_SENSOR.require_body_mm()
HALL_SENSOR_BODY_MM = HALL_SENSOR_PACKAGE_MM[:2]
HALL_SENSOR_HEIGHT_MM = HALL_SENSOR_PACKAGE_MM[2]
HALL_SENSOR_POSITION_MM = (0.0, 0.0)
HALL_SENSOR_STANDOFF_MM = 0.0
# Expander package orientation and centres are shared because the CAD proxy must
# depict the same physical obstructions that PCB placement and routing use.
_EXPANDER_PACKAGE_MM = TCA9554.require_body_mm()
EXPANDER_BODY_MM = (
    _EXPANDER_PACKAGE_MM[1],
    _EXPANDER_PACKAGE_MM[0],
    _EXPANDER_PACKAGE_MM[2],
)
HALL_BANKS = banks(GRID_COUNT)
# Lift the package above the nearest LED row, including its body and a 1 mm gap.
# This keeps the unchanged horizontal LED links out of the SOIC fanout.
EXPANDER_OFFSET_MM = (
    0.0,
    float(
        ceil(
            LED_POSITION_MM[1]
            - SQUARE_SIZE_MM / 2
            + LED_PACKAGE_MAX_SIZE_MM[1] / 2
            + EXPANDER_BODY_MM[1] / 2
            + 1.0
        )
    ),
)
EXPANDER_POSITIONS_BY_BANK_MM = MappingProxyType(
    {
        bank.label: tuple(
            a + b
            for a, b in zip(
                bank.centre(SQUARE_SIZE_MM, PLAYING_SPAN_MM),
                EXPANDER_OFFSET_MM,
                strict=True,
            )
        )
        for bank in HALL_BANKS
    }
)

# --- Printed circuit board --------------------------------------------------
# One board spans the playing area plus a 40 mm control strip along the front,
# so the buttons and display face up and solder flat like everything else.
PCB_THICKNESS_MM = 1.6
PANEL_STRIP_DEPTH_MM = 40.0
PCB_SIZE_MM = (
    PLAYING_SPAN_MM,
    PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM,
    PCB_THICKNESS_MM,
)
PCB_CENTER_OFFSET_Y_MM = -PANEL_STRIP_DEPTH_MM / 2.0

# --- Case -------------------------------------------------------------------
CASE_FRAME_WIDTH_MM = 10.0
CASE_WALL_MM = 3.0
CASE_FLOOR_MM = 3.0
# The plate rests on a ledge around the cavity, and its screws land in that
# ledge. They cannot land anywhere inboard of it, because the PCB is there.
CASE_PLATE_LEDGE_MM = 8.0
CASE_HEIGHT_MM = 30.0
CASE_OUTER_RADIUS_MM = 2.2
CASE_WIDTH_MM = PLAYING_SPAN_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_DEPTH_MM = PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM + 2.0 * CASE_FRAME_WIDTH_MM
CASE_CENTER_OFFSET_Y_MM = PCB_CENTER_OFFSET_Y_MM
CASE_OUTER_SIZE_MM = (CASE_WIDTH_MM, CASE_DEPTH_MM, CASE_HEIGHT_MM)

# Vertical stack, measured from the outside of the case floor.
TILE_PLATE_THICKNESS_MM = 3.0
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

# --- Control panel ----------------------------------------------------------
PANEL_ORIGIN_Y_MM = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0
PANEL_BUTTON_COUNT = 12
PANEL_BUTTON_COLUMNS = 6
PANEL_BUTTON_ROWS = 2
PANEL_BUTTON_HOLE_DIAMETER_MM = 7.0
PANEL_BUTTON_PITCH_MM = 16.0
PANEL_BUTTON_BLOCK_CENTER_X_MM = 40.0
PANEL_BUTTON_POSITIONS_MM = tuple(
    (
        PANEL_BUTTON_BLOCK_CENTER_X_MM
        + (column - (PANEL_BUTTON_COLUMNS - 1) / 2.0) * PANEL_BUTTON_PITCH_MM,
        PANEL_ORIGIN_Y_MM
        + ((PANEL_BUTTON_ROWS - 1) / 2.0 - row) * PANEL_BUTTON_PITCH_MM,
    )
    for row in range(PANEL_BUTTON_ROWS)
    for column in range(PANEL_BUTTON_COLUMNS)
)

# AZ-Delivery A 1-6 SH1106 1.3 in module. The window exposes the active area;
# the recess holds the carrier board, connected to J2 by four short wires.
PANEL_OLED_MODULE_MM = OLED_MODULE.require_body_mm()
PANEL_OLED_WINDOW_MM = (32.0, 18.0)
PANEL_OLED_RECESS_DEPTH_MM = 2.0
PANEL_OLED_CENTER_MM = (-110.0, PANEL_ORIGIN_Y_MM)
PANEL_BUTTON_BODY_MM = (*BUTTON.require_body_mm()[:2], 5.0)
PANEL_BUTTON_ACTUATOR_DIAMETER_MM = 3.5

# One-off electrical parts whose positions also govern enclosure access and
# populated-board collision proxies. Values are (x, y, rotation_degrees).
PCB_STRIP_PLACEMENTS_MM = MappingProxyType(
    {
        "J3": (-150.0, -178.0, -90.0),
        "F1": (-138.0, -178.0, 0.0),
        "D1": (-150.0, -165.0, 0.0),
        "SW13": (-113.0, -190.0, 0.0),
        "C1": (-128.0, -170.0, 0.0),
        "C2": (-116.0, -168.0, 0.0),
        "J2": (-95.0, -172.0, 0.0),
        "U5": (-70.0, -180.0, 0.0),
        "C7": (-58.0, -180.0, 0.0),
        "R1": (-50.0, -170.0, 0.0),
        "R2": (-50.0, -176.0, 0.0),
        "TP1": (-47.0, -165.0, 0.0),
        "TP2": (-40.0, -165.0, 0.0),
        "TP3": (-33.0, -165.0, 0.0),
        "TP4": (-26.0, -165.0, 0.0),
        "TP5": (-19.0, -165.0, 0.0),
        "TP6": (-12.0, -165.0, 0.0),
        "TP7": (-47.0, -196.0, 0.0),
    }
)

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

# --- Derived per-square positions -------------------------------------------


def _square_center(row: int, column: int) -> tuple[float, float]:
    return (
        -PLAYING_SPAN_MM / 2.0 + (column + 0.5) * SQUARE_SIZE_MM,
        PLAYING_SPAN_MM / 2.0 - (row + 0.5) * SQUARE_SIZE_MM,
    )


BOARD_SQUARE_CENTERS_MM = tuple(
    (row, column, *_square_center(row, column))
    for row in range(GRID_COUNT)
    for column in range(GRID_COUNT)
)
BOARD_LED_POSITIONS_MM = tuple(
    (row, column, x + LED_POSITION_MM[0], y + LED_POSITION_MM[1])
    for row, column, x, y in BOARD_SQUARE_CENTERS_MM
)
BOARD_HALL_POSITIONS_MM = tuple(
    (row, column, x + HALL_SENSOR_POSITION_MM[0], y + HALL_SENSOR_POSITION_MM[1])
    for row, column, x, y in BOARD_SQUARE_CENTERS_MM
)
BOARD_DARK_SQUARES_MM = tuple(
    (row, column, x, y)
    for row, column, x, y in BOARD_SQUARE_CENTERS_MM
    if (row + column) % 2 == 1
)

PRINTED_PART_SIZES_MM = (CASE_OUTER_SIZE_MM, TILE_PLATE_SIZE_MM)
LONGEST_PRINTED_PART_MM = max(max(part) for part in PRINTED_PART_SIZES_MM)
BOARD_ASSEMBLED_ENVELOPE_MM = CASE_OUTER_SIZE_MM


def meets(value: float, minimum: float) -> bool:
    """Floating-point safe "value is at least minimum".

    Derived dimensions are sums and differences of decimals, so an exact
    comparison rejects geometry that is on the limit by one part in 10^16.
    """
    return value > minimum or isclose(value, minimum, abs_tol=1e-9)


def usable_build_volume(
    build_volume_mm: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Return the build volume after reserving an edge margin on every side."""
    return tuple(axis - 2.0 * PRINT_BED_EDGE_MARGIN_MM for axis in build_volume_mm)


def fits_build_volume(
    part_dimensions_mm: tuple[float, float, float],
    build_volume_mm: tuple[float, float, float],
) -> bool:
    """Check whether an axis-aligned part fits after rotation and bed margins."""
    part = sorted(part_dimensions_mm)
    usable = sorted(usable_build_volume(build_volume_mm))
    return all(part_axis <= bed_axis for part_axis, bed_axis in zip(part, usable))


def validate() -> None:
    """Reject dimension sets that are inconsistent or physically implausible."""
    if GRID_COUNT != 8:
        raise ValueError("A chessboard must contain eight rows and eight columns")
    if BOARD_FORMAT != "compact electronic":
        raise ValueError("Review all scale guardrails when changing the board format")
    if not COMPACT_SQUARE_MIN_MM <= SQUARE_SIZE_MM <= COMPACT_SQUARE_MAX_MM:
        raise ValueError("Square size is outside the compact-board design range")
    if not isclose(PLAYING_SPAN_MM, SQUARE_SIZE_MM * GRID_COUNT):
        raise ValueError("Playing span must equal square size multiplied by grid count")
    for span in (CASE_WIDTH_MM, CASE_DEPTH_MM):
        if not COMPACT_BOARD_MIN_SPAN_MM <= span <= COMPACT_BOARD_MAX_SPAN_MM:
            raise ValueError("Case span is outside the compact product range")
    if CASE_HEIGHT_MM > COMPACT_BOARD_MAX_HEIGHT_MM:
        raise ValueError("Finished board is too tall for the compact product range")
    if not isclose(CASE_WIDTH_MM, PLAYING_SPAN_MM + 2.0 * CASE_FRAME_WIDTH_MM):
        raise ValueError("Case width must include the printed frame on both sides")
    if not isclose(
        CASE_DEPTH_MM,
        PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM + 2.0 * CASE_FRAME_WIDTH_MM,
    ):
        raise ValueError("Case depth must include the control strip and the frame")

    # The internal stack has to add up, or the plate will not sit flush.
    if not isclose(
        CASE_HEIGHT_MM,
        TILE_PLATE_THICKNESS_MM
        + PCB_TO_PLATE_GAP_MM
        + PCB_THICKNESS_MM
        + PI_BAY_HEIGHT_MM
        + CASE_FLOOR_MM,
    ):
        raise ValueError("Case height must equal the sum of the internal stack")
    if PI_BAY_HEIGHT_MM < PI_HEADER_HEIGHT_MM + PI_BOARD_SIZE_MM[2] + PI_CLEARANCE_MM:
        raise ValueError(
            "Cavity below the board is too shallow for the Pi on its header"
        )
    tallest_playing_area_component = max(
        HALL_SENSOR_HEIGHT_MM + HALL_SENSOR_STANDOFF_MM,
        LED_PACKAGE_MAX_SIZE_MM[2],
        EXPANDER_BODY_MM[2],
    )
    if PCB_TO_PLATE_GAP_MM < tallest_playing_area_component:
        raise ValueError("Plate would foul a component in the playing area")

    if (
        not FDM_MIN_FIT_CLEARANCE_MM
        <= TILE_PLATE_CLEARANCE_MM
        <= (FDM_MAX_FIT_CLEARANCE_MM)
    ):
        raise ValueError("Tile plate clearance is outside the prototype fit range")

    minimum_features = {
        "case wall": CASE_WALL_MM,
        "case floor": CASE_FLOOR_MM,
        "case frame": CASE_FRAME_WIDTH_MM,
        "plate thickness": TILE_PLATE_THICKNESS_MM,
        "plate diffuser skin": TILE_PLATE_DIFFUSER_SKIN_MM,
        "plate rib": TILE_PLATE_RIB_WIDTH_MM,
        "plate pocket floor": TILE_PLATE_THICKNESS_MM
        - TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM
        - TILE_PLATE_DARK_SQUARE_DEPTH_MM,
        "plate groove": TILE_PLATE_GROOVE_WIDTH_MM,
        "support boss wall": (
            PCB_SUPPORT_BOSS_DIAMETER_MM - PCB_SUPPORT_PILOT_DIAMETER_MM
        )
        / 2.0,
    }
    for name, dimension in minimum_features.items():
        minimum = FDM_MIN_FLOOR_MM if name.endswith("floor") else FDM_MIN_FEATURE_MM
        if not meets(dimension, minimum):
            raise ValueError(f"{name} is below the prototype printable minimum")

    if TILE_PLATE_LED_POCKET_MM[2] >= TILE_PLATE_THICKNESS_MM:
        raise ValueError("LED pocket must leave a closed diffuser skin")
    if TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM >= (
        TILE_PLATE_THICKNESS_MM - FDM_MIN_FLOOR_MM
    ):
        raise ValueError("Underside pockets must leave a printable plate floor")
    if TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM <= HALL_SENSOR_BODY_MM[0]:
        raise ValueError("Underside pocket must span the Hall sensor it clears")
    if TILE_PLATE_DARK_SQUARE_DEPTH_MM >= TILE_PLATE_DIFFUSER_SKIN_MM:
        raise ValueError("Dark-square recess must not reach the diffuser skin")
    required_led_pocket_xy = tuple(
        package + 2.0 * LED_PACKAGE_CLEARANCE_PER_SIDE_MM
        for package in LED_PACKAGE_MAX_SIZE_MM[:2]
    )
    if any(
        pocket < required
        for pocket, required in zip(
            TILE_PLATE_LED_POCKET_MM[:2], required_led_pocket_xy
        )
    ):
        raise ValueError("LED pocket does not clear the maximum 5050 package")
    if any(
        pocket < emitter + LED_PACKAGE_TOLERANCE_MM
        for pocket, emitter in zip(TILE_PLATE_LED_POCKET_MM[:2], LED_EMITTER_WINDOW_MM)
    ):
        raise ValueError("LED pocket does not clear the emitter window")
    if not meets(
        TILE_PLATE_DIFFUSER_SKIN_MM - TILE_PLATE_DARK_SQUARE_DEPTH_MM,
        FDM_MIN_FEATURE_MM,
    ):
        raise ValueError(
            "A dark square over an LED pocket would leave too thin a diffuser"
        )
    if TILE_PLATE_SCREW_HEAD_DIAMETER_MM <= TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM:
        raise ValueError("Screw head recess must be wider than its clearance hole")
    if TILE_PLATE_SCREW_HEAD_DEPTH_MM >= TILE_PLATE_THICKNESS_MM:
        raise ValueError("Screw head recess must leave a bearing shoulder")

    # Every plate screw has to land on the case ledge. Anywhere inboard of it is
    # over the PCB, and a boss there would collide with the board.
    ledge_inner = PLAYING_SPAN_MM / 2.0 - CASE_PLATE_LEDGE_MM
    ledge_outer = PLAYING_SPAN_MM / 2.0
    screw_radius = TILE_PLATE_SCREW_HEAD_DIAMETER_MM / 2.0
    for screw_x, screw_y in TILE_PLATE_SCREW_POSITIONS_MM:
        reach = max(abs(screw_x), abs(screw_y))
        if not ledge_inner + screw_radius <= reach <= ledge_outer - screw_radius:
            raise ValueError("A tile plate screw does not land on the case ledge")
    if len(set(TILE_PLATE_SCREW_POSITIONS_MM)) != len(TILE_PLATE_SCREW_POSITIONS_MM):
        raise ValueError("Tile plate screw positions must be unique")
    if CASE_PLATE_LEDGE_MM <= TILE_PLATE_CLEARANCE_MM:
        raise ValueError("The plate ledge must be wider than the plate's own clearance")

    # Per-square features must stay inside their own square, or two squares
    # would light or sense as one.
    half = SQUARE_SIZE_MM / 2.0
    for axis, position in enumerate(LED_POSITION_MM):
        margin = half - abs(position) - TILE_PLATE_LED_POCKET_MM[axis] / 2.0
        if margin < FDM_MIN_FEATURE_MM:
            raise ValueError("LED pocket crosses into the neighbouring square")
    if HALL_SENSOR_BODY_MM[0] > SQUARE_SIZE_MM - 2.0 * FDM_MIN_FEATURE_MM:
        raise ValueError("Hall sensor body does not fit within one square")

    # Support bosses stand on the grid lines; nothing else may be there.
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss_x, boss_y in PCB_SUPPORT_POSITIONS_MM:
        for _row, _column, led_x, led_y in BOARD_LED_POSITIONS_MM:
            gap = max(abs(boss_x - led_x), abs(boss_y - led_y))
            if gap < boss_radius + TILE_PLATE_LED_POCKET_MM[0] / 2.0:
                raise ValueError("A support boss collides with an LED position")
        for _row, _column, sensor_x, sensor_y in BOARD_HALL_POSITIONS_MM:
            if (
                abs(boss_x - sensor_x) < boss_radius + HALL_SENSOR_BODY_MM[0] / 2.0
                and abs(boss_y - sensor_y) < boss_radius + HALL_SENSOR_BODY_MM[1] / 2.0
            ):
                raise ValueError("A support boss collides with a Hall sensor")
    if len(set(PCB_SUPPORT_POSITIONS_MM)) != len(PCB_SUPPORT_POSITIONS_MM):
        raise ValueError("Support boss positions must be unique")
    if PCB_SUPPORT_PILOT_DEPTH_MM >= PCB_SUPPORT_BOSS_DIAMETER_MM * 3.0:
        raise ValueError("Support pilot is too deep for its boss")

    # Control panel features must stay on the control strip.
    strip_min_y = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM
    strip_max_y = -PLAYING_SPAN_MM / 2.0
    panel_features: tuple[tuple[str, float, float, float, float], ...] = tuple(
        (
            "button",
            x,
            y,
            PANEL_BUTTON_HOLE_DIAMETER_MM / 2.0,
            PANEL_BUTTON_HOLE_DIAMETER_MM / 2.0,
        )
        for x, y in PANEL_BUTTON_POSITIONS_MM
    ) + (
        (
            "display",
            PANEL_OLED_CENTER_MM[0],
            PANEL_OLED_CENTER_MM[1],
            PANEL_OLED_MODULE_MM[0] / 2.0,
            PANEL_OLED_MODULE_MM[1] / 2.0,
        ),
    )
    for name, x, y, half_x, half_y in panel_features:
        if not strip_min_y <= y - half_y and y + half_y <= strip_max_y:
            raise ValueError(f"Control panel {name} extends off the control strip")
        if abs(x) + half_x > PLAYING_SPAN_MM / 2.0:
            raise ValueError(f"Control panel {name} extends off the board")
    if len(PANEL_BUTTON_POSITIONS_MM) != PANEL_BUTTON_COUNT:
        raise ValueError("Control panel must place every button")
    if len(set(PANEL_BUTTON_POSITIONS_MM)) != PANEL_BUTTON_COUNT:
        raise ValueError("Button positions must be unique")
    if any(
        window >= module
        for window, module in zip(PANEL_OLED_WINDOW_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display window must be smaller than the module behind it")

    if len(EXPANDER_POSITIONS_BY_BANK_MM) != 8:
        raise ValueError("Board composition must place eight GPIO expanders")
    if len(set(EXPANDER_POSITIONS_BY_BANK_MM.values())) != 8:
        raise ValueError("GPIO expander positions must be unique")

    for name, count in (
        ("LED", len(BOARD_LED_POSITIONS_MM)),
        ("hall", len(BOARD_HALL_POSITIONS_MM)),
    ):
        if count != GRID_COUNT * GRID_COUNT:
            raise ValueError(f"Board composition must contain one {name} per square")
    if len({(x, y) for _r, _c, x, y in BOARD_LED_POSITIONS_MM}) != GRID_COUNT**2:
        raise ValueError("Every composed LED position must be unique")
    if len(BOARD_DARK_SQUARES_MM) != GRID_COUNT * GRID_COUNT // 2:
        raise ValueError("A checkerboard must have half its squares dark")

    if not isclose(PCB_SIZE_MM[0], PLAYING_SPAN_MM):
        raise ValueError("Board must be exactly as wide as the playing area")
    if not isclose(PCB_SIZE_MM[1], PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM):
        raise ValueError("Board must carry the playing area and the control strip")

    for part_size in PRINTED_PART_SIZES_MM:
        if not fits_build_volume(part_size, REFERENCE_SERVICE_BUILD_VOLUME_MM):
            raise ValueError(
                "A printed part exceeds the print-service reference volume"
            )


def describe(domain: str = "Shared hardware") -> str:
    """Return a compact summary suitable for domain validation commands."""
    return (
        f"{domain} dimensions valid: "
        f"{GRID_COUNT} x {SQUARE_SIZE_MM:g} mm = {PLAYING_SPAN_MM:g} mm playing span; "
        f"case {CASE_WIDTH_MM:g} x {CASE_DEPTH_MM:g} x {CASE_HEIGHT_MM:g} mm "
        f"({CASE_DEPTH_MM / MILLIMETRES_PER_INCH:.1f} in deep); "
        f"plate {TILE_PLATE_SPAN_MM:g} mm; "
        f"board {PCB_SIZE_MM[0]:g} x {PCB_SIZE_MM[1]:g} mm"
    )


# Re-export public measurements through thin domain adapters without leaking
# implementation imports such as ``isclose``.
__all__ = tuple(
    name for name in globals() if name.isupper() and not name.startswith("_")
) + (
    "describe",
    "fits_build_volume",
    "meets",
    "usable_build_volume",
    "validate",
)

validate()


if __name__ == "__main__":
    print(describe())
