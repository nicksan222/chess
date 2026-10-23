"""Cross-part physical validation and dimension summaries.

Role: checks that the separately defined dimensions fit one another: the stack sums to the
case height, the board fits its pocket with ledge bearing on every side, screws land on
the rim, button stems protrude within limits, panel parts and the Pi stay inside their bay
and away from bosses. `validate()` runs on import of `shared.dimensions`; the
`validate_*` helpers are focused checks it calls. A failure is a real dimension error, so
fix the source values rather than weaken a check. `describe()` gives the one-line summary
printed by the shared and CAD check recipes.
"""

from math import isclose

from shared.panel_buttons import PANEL_BUTTONS

from .board import (
    BOARD_FORMAT,
    BOARD_SQUARES,
    COMPACT_BOARD_MAX_HEIGHT_MM,
    COMPACT_BOARD_MAX_SPAN_MM,
    COMPACT_BOARD_MIN_SPAN_MM,
    COMPACT_SQUARE_MAX_MM,
    COMPACT_SQUARE_MIN_MM,
    EXPANDER_BODY_MM,
    EXPANDER_POSITIONS_BY_BANK_MM,
    GRID_COUNT,
    HALL_SENSOR_BODY_MM,
    HALL_SENSOR_HEIGHT_MM,
    HALL_SENSOR_STANDOFF_MM,
    LED_EMITTER_WINDOW_MM,
    LED_PACKAGE_CLEARANCE_PER_SIDE_MM,
    LED_PACKAGE_MAX_SIZE_MM,
    LED_PACKAGE_TOLERANCE_MM,
    LED_POSITION_MM,
    PANEL_STRIP_DEPTH_MM,
    PCB_BOTTOM_EDGE_KEEPOUT_MM,
    PCB_CENTER_OFFSET_Y_MM,
    PCB_SIZE_MM,
    PCB_THICKNESS_MM,
    PLAYING_SPAN_MM,
    SQUARE_SIZE_MM,
)
from .case import (
    BOTTOM_SIDE_KEEPOUTS_MM,
    CASE_CAVITY_SIZE_MM,
    CASE_CENTER_OFFSET_Y_MM,
    CASE_DEPTH_MM,
    CASE_FLOOR_MM,
    CASE_FRAME_WIDTH_MM,
    CASE_HEIGHT_MM,
    CASE_JACK_APERTURE_CENTER_X_MM,
    CASE_JACK_APERTURE_DIAMETER_MM,
    CASE_JACK_BUSHING_DIAMETER_MM,
    CASE_JACK_FLANGE_DIAMETER_MM,
    CASE_JACK_MAX_PANEL_MM,
    CASE_JACK_PANEL_THICKNESS_MM,
    CASE_JACK_POCKET_WIDTH_MM,
    CASE_PCB_LEDGE_OVERLAP_MM,
    CASE_PLATE_LEDGE_MM,
    CASE_PLATE_REBATE_MM,
    CASE_REAR_APERTURE_CENTER_Z_MM,
    CASE_ROCKER_APERTURE_CENTER_X_MM,
    CASE_ROCKER_APERTURE_MM,
    CASE_ROCKER_CUTOUT_MM,
    CASE_ROCKER_LATCH_MARGIN_MM,
    CASE_ROCKER_PANEL_RANGE_MM,
    CASE_ROCKER_PANEL_THICKNESS_MM,
    CASE_ROCKER_POCKET_ROOF_MM,
    CASE_ROCKER_POCKET_WIDTH_MM,
    CASE_ROCKER_POCKET_Z_MM,
    CASE_SD_PANEL_THICKNESS_MM,
    CASE_SD_SLOT_CENTER_Y_MM,
    CASE_SD_SLOT_CENTER_Z_MM,
    CASE_SD_SLOT_MM,
    CASE_WALL_MM,
    CASE_WALL_POCKET_Z_MM,
    CASE_WIDTH_MM,
    PCB_POCKET_CLEARANCE_MM,
    PCB_POCKET_SIZE_MM,
    PCB_SUPPORT_BOSS_DIAMETER_MM,
    PCB_SUPPORT_PILOT_DEPTH_MM,
    PCB_SUPPORT_PILOT_DIAMETER_MM,
    PCB_SUPPORT_POSITIONS_MM,
    PCB_TO_PLATE_GAP_MM,
    PCB_TOP_Z_MM,
    PCB_UNDERSIDE_Z_MM,
    PI_BAY_HEIGHT_MM,
    PI_BOARD_SIZE_MM,
    PI_BOARD_TO_BOARD_MM,
    PI_CENTER_MM,
    PI_CLEARANCE_MM,
    PI_HEADER_PIN_COUNT,
    PI_ROTATION_DEG,
    PI_SD_SOCKET_ON_PI_MM,
    pi_header_pin_xy,
    pi_on_board_xy,
)
from .panel import (
    PANEL_BUTTON_ACTUATOR_DIAMETER_MM,
    PANEL_BUTTON_BODY_MM,
    PANEL_BUTTON_CAP_BOTTOM_Z_MM,
    PANEL_BUTTON_CAP_SIZE_MM,
    PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM,
    PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM,
    PANEL_BUTTON_COUNT,
    PANEL_BUTTON_HEIGHT_MM,
    PANEL_BUTTON_HOLE_DIAMETER_MM,
    PANEL_BUTTON_MAX_PROTRUSION_MM,
    PANEL_BUTTON_MIN_PROTRUSION_MM,
    PANEL_BUTTON_RELIEF_CLEARANCE_MM,
    PANEL_BUTTON_RELIEF_DEPTH_MM,
    PANEL_OLED_BEZEL_CLEARANCE_XY_MM,
    PANEL_OLED_BEZEL_INNER_MM,
    PANEL_OLED_BEZEL_OUTER_MM,
    PANEL_OLED_BEZEL_ROOF_MM,
    PANEL_OLED_BEZEL_WALL_MM,
    PANEL_OLED_CENTER_MM,
    PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM,
    PANEL_OLED_LEDGE_BOTTOM_Z_MM,
    PANEL_OLED_LEDGE_WIDTH_MM,
    PANEL_OLED_MODULE_MM,
    PANEL_OLED_MOUNT_HOLES_MM,
    PANEL_OLED_PCB_BOTTOM_Z_MM,
    PANEL_OLED_PCB_THICKNESS_MM,
    PANEL_OLED_PILOT_DIAMETER_MM,
    PANEL_OLED_PILOT_FLOOR_MM,
    PANEL_OLED_SCREEN_SIZE_MM,
    PANEL_OLED_SCREEN_Z_MM,
    PANEL_OLED_SCREW_HEAD_DIAMETER_MM,
    PANEL_OLED_SCREW_HEAD_HEIGHT_MM,
    PANEL_OLED_SCREW_LENGTH_MM,
    PANEL_OLED_WIRE_OPENING_MM,
    PANEL_SURFACE_RECESS_MM,
)
from .printing import (
    FDM_MAX_FIT_CLEARANCE_MM,
    FDM_MIN_FEATURE_MM,
    FDM_MIN_FIT_CLEARANCE_MM,
    FDM_MIN_FLOOR_MM,
    PRINTED_PART_SIZES_MM,
    REFERENCE_SERVICE_BUILD_VOLUME_MM,
    fits_build_volume,
    meets,
)
from .tile_plate import (
    PIECE_LOCATING_FOOT_HEIGHT_MM,
    PIECE_LOCATING_FOOT_INNER_SIDE_MM,
    PIECE_LOCATING_FOOT_SIDE_MM,
    TILE_PLATE_CENTER_Y_MM,
    TILE_PLATE_CLEARANCE_MM,
    TILE_PLATE_DARK_SQUARE_DEPTH_MM,
    TILE_PLATE_DIFFUSER_SKIN_MM,
    TILE_PLATE_GROOVE_WIDTH_MM,
    TILE_PLATE_LED_POCKET_MM,
    TILE_PLATE_LED_WINDOW_MM,
    TILE_PLATE_PIECE_SEAT_DEPTH_MM,
    TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM,
    TILE_PLATE_PIECE_SEAT_SIDE_MM,
    TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM,
    TILE_PLATE_RIB_WIDTH_MM,
    TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM,
    TILE_PLATE_SCREW_HEAD_DEPTH_MM,
    TILE_PLATE_SCREW_HEAD_DIAMETER_MM,
    TILE_PLATE_SCREW_POSITIONS_MM,
    TILE_PLATE_SIZE_MM,
    TILE_PLATE_THICKNESS_MM,
    TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM,
    TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM,
)
from .units import (
    MILLIMETRES_PER_INCH,
)


# Named limits that used to be bare literals inside the checks.
EXPECTED_GRID_COUNT = 8  # a chessboard has eight rows and eight columns
GPIO_EXPANDER_COUNT = 8  # one expander per Hall bank
SUPPORT_PILOT_MAX_BOSS_RATIO = 3.0  # pilot depth limit, in boss diameters
OLED_SCREW_HEAD_SLACK_MM = 0.1  # head may rise this far into the bezel roof
SD_SLOT_TOLERANCE_MM = 1e-9  # slot/socket alignment and Pi reach tolerance


def require(condition: bool, message: str) -> None:
    """Raise `ValueError(message)` unless `condition` holds."""
    if not condition:
        raise ValueError(message)


def require_meets(value: float, minimum: float, message: str) -> None:
    """Require `value` to be at least `minimum`, tolerant of float rounding."""
    require(meets(value, minimum), message)


def require_between(value: float, low: float, high: float, message: str) -> None:
    """Require `low <= value <= high`."""
    require(low <= value <= high, message)


def _validate_case_envelope() -> None:
    """The grid, the compact-product ranges and the case outline."""
    require(
        GRID_COUNT == EXPECTED_GRID_COUNT,
        "A chessboard must contain eight rows and eight columns",
    )
    require(
        BOARD_FORMAT == "compact electronic",
        "Review all scale guardrails when changing the board format",
    )
    require_between(
        SQUARE_SIZE_MM,
        COMPACT_SQUARE_MIN_MM,
        COMPACT_SQUARE_MAX_MM,
        "Square size is outside the compact-board design range",
    )
    require(
        isclose(PLAYING_SPAN_MM, SQUARE_SIZE_MM * GRID_COUNT),
        "Playing span must equal square size multiplied by grid count",
    )
    for span in (CASE_WIDTH_MM, CASE_DEPTH_MM):
        require_between(
            span - 2 * CASE_FRAME_WIDTH_MM,
            COMPACT_BOARD_MIN_SPAN_MM,
            COMPACT_BOARD_MAX_SPAN_MM,
            "Case span is outside the compact product range",
        )
    require(
        CASE_HEIGHT_MM <= COMPACT_BOARD_MAX_HEIGHT_MM,
        "Finished board is too tall for the compact product range",
    )
    require(
        isclose(CASE_WIDTH_MM, PLAYING_SPAN_MM + 2.0 * CASE_FRAME_WIDTH_MM),
        "Case width must include the printed frame on both sides",
    )
    require(
        isclose(
            CASE_DEPTH_MM,
            PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM + 2.0 * CASE_FRAME_WIDTH_MM,
        ),
        "Case depth must include the control strip and the frame",
    )


def _validate_stack() -> None:
    """The internal stack has to add up, or the plate will not sit flush."""
    require(
        isclose(
            CASE_HEIGHT_MM,
            TILE_PLATE_THICKNESS_MM
            + PCB_TO_PLATE_GAP_MM
            + PCB_THICKNESS_MM
            + PI_BAY_HEIGHT_MM
            + CASE_FLOOR_MM,
        ),
        "Case height must equal the sum of the internal stack",
    )
    require(
        PI_BAY_HEIGHT_MM
        >= PI_BOARD_TO_BOARD_MM + PI_BOARD_SIZE_MM[2] + PI_CLEARANCE_MM,
        "Cavity below the board is too shallow for the Pi on its header",
    )
    tallest_playing_area_component = max(
        HALL_SENSOR_HEIGHT_MM + HALL_SENSOR_STANDOFF_MM,
        LED_PACKAGE_MAX_SIZE_MM[2],
        EXPANDER_BODY_MM[2],
    )
    require(
        PCB_TO_PLATE_GAP_MM >= tallest_playing_area_component,
        "Plate would foul a component in the playing area",
    )
    require_between(
        TILE_PLATE_CLEARANCE_MM,
        FDM_MIN_FIT_CLEARANCE_MM,
        FDM_MAX_FIT_CLEARANCE_MM,
        "Tile plate clearance is outside the prototype fit range",
    )


def _validate_printable_minimums() -> None:
    """Every named feature meets the prototype FDM minimum."""
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
        require_meets(
            dimension, minimum, f"{name} is below the prototype printable minimum"
        )


def _validate_plate_features() -> None:
    """LED pockets, underside pockets, dark squares and screw recesses of the plate."""
    require(
        TILE_PLATE_LED_POCKET_MM[2] < TILE_PLATE_THICKNESS_MM,
        "LED pocket must retain a roof around the open window",
    )
    require(
        TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM
        < TILE_PLATE_THICKNESS_MM - FDM_MIN_FLOOR_MM,
        "Underside pockets must leave a printable plate floor",
    )
    require(
        TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM > HALL_SENSOR_BODY_MM[0],
        "Underside pocket must span the Hall sensor it clears",
    )
    require(
        TILE_PLATE_DARK_SQUARE_DEPTH_MM < TILE_PLATE_DIFFUSER_SKIN_MM,
        "Dark-square recess must not reach the diffuser skin",
    )
    required_led_pocket_xy = tuple(
        package + 2.0 * LED_PACKAGE_CLEARANCE_PER_SIDE_MM
        for package in LED_PACKAGE_MAX_SIZE_MM[:2]
    )
    require(
        not any(
            pocket < required
            for pocket, required in zip(
                TILE_PLATE_LED_POCKET_MM[:2], required_led_pocket_xy
            )
        ),
        "LED pocket does not clear the maximum 5050 package",
    )
    require(
        not any(
            pocket < emitter + LED_PACKAGE_TOLERANCE_MM
            for pocket, emitter in zip(
                TILE_PLATE_LED_POCKET_MM[:2], LED_EMITTER_WINDOW_MM
            )
        ),
        "LED pocket does not clear the emitter window",
    )
    require_meets(
        TILE_PLATE_DIFFUSER_SKIN_MM - TILE_PLATE_DARK_SQUARE_DEPTH_MM,
        FDM_MIN_FEATURE_MM,
        "A dark square over an LED pocket would leave too thin a diffuser",
    )
    require(
        TILE_PLATE_SCREW_HEAD_DIAMETER_MM > TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM,
        "Screw head recess must be wider than its clearance hole",
    )
    require(
        TILE_PLATE_SCREW_HEAD_DEPTH_MM < TILE_PLATE_THICKNESS_MM,
        "Screw head recess must leave a bearing shoulder",
    )


def _validate_pocket_and_rim() -> None:
    """The board pocket, the plate rim and the ledge between them."""
    validate_board_pocket()
    validate_plate_rim()
    require(
        CASE_PLATE_LEDGE_MM > TILE_PLATE_CLEARANCE_MM,
        "The plate ledge must be wider than the plate's own clearance",
    )


def _validate_square_isolation() -> None:
    """Per-square features stay inside their own square.

    Otherwise two squares would light or sense as one.
    """
    half = SQUARE_SIZE_MM / 2.0
    for axis, position in enumerate(LED_POSITION_MM):
        margin = half - abs(position) - TILE_PLATE_LED_POCKET_MM[axis] / 2.0
        require(
            not margin < FDM_MIN_FEATURE_MM,
            "LED pocket crosses into the neighbouring square",
        )
    require(
        not HALL_SENSOR_BODY_MM[0] > SQUARE_SIZE_MM - 2.0 * FDM_MIN_FEATURE_MM,
        "Hall sensor body does not fit within one square",
    )


def _validate_support_bosses() -> None:
    """Support bosses stand on the grid lines; nothing else may be there."""
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss_x, boss_y in PCB_SUPPORT_POSITIONS_MM:
        for led_x, led_y in (square.led_position_mm for square in BOARD_SQUARES):
            gap = max(abs(boss_x - led_x), abs(boss_y - led_y))
            require(
                not gap < boss_radius + TILE_PLATE_LED_POCKET_MM[0] / 2.0,
                "A support boss collides with an LED position",
            )
        for sensor_x, sensor_y in (square.hall_position_mm for square in BOARD_SQUARES):
            require(
                not (
                    abs(boss_x - sensor_x) < boss_radius + HALL_SENSOR_BODY_MM[0] / 2.0
                    and abs(boss_y - sensor_y)
                    < boss_radius + HALL_SENSOR_BODY_MM[1] / 2.0
                ),
                "A support boss collides with a Hall sensor",
            )
    require(
        len(set(PCB_SUPPORT_POSITIONS_MM)) == len(PCB_SUPPORT_POSITIONS_MM),
        "Support boss positions must be unique",
    )
    require(
        PCB_SUPPORT_PILOT_DEPTH_MM
        < PCB_SUPPORT_BOSS_DIAMETER_MM * SUPPORT_PILOT_MAX_BOSS_RATIO,
        "Support pilot is too deep for its boss",
    )


def _validate_control_panel() -> None:
    """Control panel features stay on the control strip; the display recess fits."""
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
        for x, y in (button.position_mm for button in PANEL_BUTTONS)
    ) + (
        (
            "display",
            PANEL_OLED_CENTER_MM[0],
            PANEL_OLED_CENTER_MM[1],
            PANEL_OLED_BEZEL_OUTER_MM[0] / 2.0,
            PANEL_OLED_BEZEL_OUTER_MM[1] / 2.0,
        ),
    )
    for name, x, y, half_x, half_y in panel_features:
        require(
            strip_min_y <= y - half_y and y + half_y <= strip_max_y,
            f"Control panel {name} extends off the control strip",
        )
        require(
            not abs(x) + half_x > PLAYING_SPAN_MM / 2.0,
            f"Control panel {name} extends off the board",
        )
    require(
        len(PANEL_BUTTONS) == PANEL_BUTTON_COUNT,
        "Control panel must place every button",
    )
    require(
        len({button.position_mm for button in PANEL_BUTTONS}) == PANEL_BUTTON_COUNT,
        "Button positions must be unique",
    )
    require(
        PANEL_OLED_BEZEL_CLEARANCE_XY_MM > 0.0,
        "Display recess must include positive XY assembly clearance",
    )
    require(
        not any(
            recess <= module
            for recess, module in zip(
                PANEL_OLED_BEZEL_INNER_MM, PANEL_OLED_MODULE_MM[:2]
            )
        ),
        "Display recess must be larger than the module",
    )
    require(
        not any(
            window >= module
            for window, module in zip(
                PANEL_OLED_SCREEN_SIZE_MM, PANEL_OLED_MODULE_MM[:2]
            )
        ),
        "Display window must be smaller than the module behind it",
    )


def _validate_led_windows() -> None:
    """Each LED window exposes its emitter and keeps a printable roof."""
    for aperture, emitter, pocket in zip(
        TILE_PLATE_LED_WINDOW_MM, LED_EMITTER_WINDOW_MM, TILE_PLATE_LED_POCKET_MM[:2]
    ):
        require(
            not aperture < emitter + LED_PACKAGE_TOLERANCE_MM,
            "LED window must expose the whole emitter",
        )
        require_meets(
            (pocket - aperture) / 2,
            FDM_MIN_FEATURE_MM,
            "LED window must retain a printable surrounding roof",
        )


def _validate_display_mount() -> None:
    """The control surface recess, the display screws and the bezel walls."""
    require(
        0 < PANEL_SURFACE_RECESS_MM < TILE_PLATE_THICKNESS_MM,
        "Control surface must be recessed within the plate",
    )
    screw_tip = (
        PANEL_OLED_PCB_BOTTOM_Z_MM
        + PANEL_OLED_PCB_THICKNESS_MM
        - PANEL_OLED_SCREW_LENGTH_MM
    )
    require_meets(
        screw_tip - (PANEL_OLED_LEDGE_BOTTOM_Z_MM + PANEL_OLED_PILOT_FLOOR_MM),
        FDM_MIN_FIT_CLEARANCE_MM,
        "Display screw would bottom out in its blind pilot",
    )
    require_meets(
        (PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM - PANEL_OLED_SCREW_HEAD_DIAMETER_MM)
        / 2,
        FDM_MIN_FIT_CLEARANCE_MM,
        "Display access must clear the screw head",
    )
    require(
        not PANEL_OLED_PCB_BOTTOM_Z_MM
        + PANEL_OLED_PCB_THICKNESS_MM
        + PANEL_OLED_SCREW_HEAD_HEIGHT_MM
        > PANEL_OLED_SCREEN_Z_MM + OLED_SCREW_HEAD_SLACK_MM,
        "Display screw head does not fit below the bezel roof",
    )
    for dx, dy in PANEL_OLED_MOUNT_HOLES_MM:
        for center, span in zip((dx, dy), PANEL_OLED_BEZEL_OUTER_MM):
            require_meets(
                span / 2 - abs(center) - PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM / 2,
                FDM_MIN_FEATURE_MM,
                "Display access hole leaves too thin a bezel edge",
            )
    require_meets(
        (PANEL_OLED_LEDGE_WIDTH_MM - PANEL_OLED_PILOT_DIAMETER_MM) / 2,
        FDM_MIN_FEATURE_MM,
        "Display mounting pilot needs printable surrounding walls",
    )
    require(
        not PANEL_OLED_PCB_BOTTOM_Z_MM - PANEL_OLED_LEDGE_BOTTOM_Z_MM
        <= PANEL_OLED_PILOT_FLOOR_MM,
        "Display mounting pilot needs depth above its floor",
    )
    require_meets(
        PANEL_OLED_PILOT_FLOOR_MM,
        FDM_MIN_FLOOR_MM,
        "Display mounting pilot must retain a printable floor",
    )
    require(
        meets(PANEL_OLED_BEZEL_WALL_MM, FDM_MIN_FEATURE_MM)
        and meets(PANEL_OLED_BEZEL_ROOF_MM, FDM_MIN_FEATURE_MM),
        "Display bezel needs printable walls and roof",
    )
    require(
        not any(
            wire >= body
            for wire, body in zip(PANEL_OLED_WIRE_OPENING_MM, PANEL_OLED_MODULE_MM[:2])
        ),
        "Display wire opening must leave supporting material",
    )


def _validate_part_checks() -> None:
    """The focused per-part checks, in the order they have always run."""
    validate_piece_seats()
    validate_buttons()
    validate_rocker()
    validate_jack()
    validate_pi_bay()
    validate_bottom_keepouts()
    validate_sd_slot()


def _validate_board_composition() -> None:
    """Expanders, square topology and the PCB outline."""
    require(
        len(EXPANDER_POSITIONS_BY_BANK_MM) == GPIO_EXPANDER_COUNT,
        "Board composition must place eight GPIO expanders",
    )
    require(
        len(set(EXPANDER_POSITIONS_BY_BANK_MM.values())) == GPIO_EXPANDER_COUNT,
        "GPIO expander positions must be unique",
    )

    BOARD_SQUARES.validate_topology()

    require(
        isclose(PCB_SIZE_MM[0], PLAYING_SPAN_MM),
        "Board must be exactly as wide as the playing area",
    )
    require(
        isclose(PCB_SIZE_MM[1], PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM),
        "Board must carry the playing area and the control strip",
    )


def _validate_build_volume() -> None:
    """Every printed part fits the print-service reference volume."""
    for part_size in PRINTED_PART_SIZES_MM:
        require(
            fits_build_volume(part_size, REFERENCE_SERVICE_BUILD_VOLUME_MM),
            "A printed part exceeds the print-service reference volume",
        )


# Run in this order: the first failing check names the error, so reordering changes
# which message a multiply-wrong dimension set reports.
_CHECKS = (
    _validate_case_envelope,
    _validate_stack,
    _validate_printable_minimums,
    _validate_plate_features,
    _validate_pocket_and_rim,
    _validate_square_isolation,
    _validate_support_bosses,
    _validate_control_panel,
    _validate_led_windows,
    _validate_display_mount,
    _validate_part_checks,
    _validate_board_composition,
    _validate_build_volume,
)


def validate() -> None:
    """Reject dimension sets that are inconsistent or physically implausible."""
    for check in _CHECKS:
        check()


Point = tuple[float, float]


# Axis-aligned rectangle test used by the bay and keep-out checks.
def _outside(point: Point, centre: Point, size: tuple[float, float]) -> float:
    """Distance outside an axis-aligned rectangle; negative means inside."""
    return max(
        abs(point[0] - centre[0]) - size[0] / 2.0,
        abs(point[1] - centre[1]) - size[1] / 2.0,
    )


def validate_board_pocket() -> None:
    """The board drops into its pocket and rests on a ledge on all four sides."""
    require_between(
        PCB_POCKET_CLEARANCE_MM,
        FDM_MIN_FIT_CLEARANCE_MM,
        FDM_MAX_FIT_CLEARANCE_MM,
        "PCB pocket clearance is outside the prototype fit range",
    )
    require(
        isclose(PCB_CENTER_OFFSET_Y_MM, CASE_CENTER_OFFSET_Y_MM),
        "The PCB pocket must be centred on the board",
    )
    for axis, outer in enumerate((CASE_WIDTH_MM, CASE_DEPTH_MM)):
        require(
            isclose(
                PCB_POCKET_SIZE_MM[axis],
                PCB_SIZE_MM[axis] + 2.0 * PCB_POCKET_CLEARANCE_MM,
            ),
            "PCB pocket must be the board outline plus clearance",
        )
        require_meets(
            (outer - PCB_POCKET_SIZE_MM[axis]) / 2.0,
            CASE_WALL_MM,
            "Case wall outboard of the PCB pocket is too thin",
        )
        # The board can float by the clearance; with it pushed fully away from a
        # side, the ledge on that side must still carry it.
        for side in (-1.0, 1.0):
            board_edge = side * PCB_SIZE_MM[axis] / 2.0
            cavity_edge = side * CASE_CAVITY_SIZE_MM[axis] / 2.0
            bearing = side * (board_edge - cavity_edge) - PCB_POCKET_CLEARANCE_MM
            require_meets(
                bearing,
                FDM_MIN_FEATURE_MM,
                "The PCB ledge does not support every board edge",
            )
    require_meets(
        PCB_BOTTOM_EDGE_KEEPOUT_MM,
        CASE_PCB_LEDGE_OVERLAP_MM + PCB_POCKET_CLEARANCE_MM,
        "The PCB ledge reaches past the bottom-side edge keepout",
    )
    cavity_centre = (0.0, CASE_CENTER_OFFSET_Y_MM)
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss in PCB_SUPPORT_POSITIONS_MM:
        require(
            not _outside(boss, cavity_centre, CASE_CAVITY_SIZE_MM) > -boss_radius,
            "A support boss is not inside the cavity under the board",
        )


def validate_plate_rim() -> None:
    """The plate rests on a rim outboard of the PCB pocket, held by screws there."""
    require(
        isclose(TILE_PLATE_CENTER_Y_MM, CASE_CENTER_OFFSET_Y_MM),
        "The plate must be centred on the case",
    )
    for axis, outer in enumerate((CASE_WIDTH_MM, CASE_DEPTH_MM)):
        require(
            isclose(
                CASE_PLATE_REBATE_MM[axis],
                TILE_PLATE_SIZE_MM[axis] + TILE_PLATE_CLEARANCE_MM,
            ),
            "The plate rebate must be the plate plus its clearance",
        )
        require(
            isclose(
                (TILE_PLATE_SIZE_MM[axis] - PCB_POCKET_SIZE_MM[axis]) / 2.0,
                CASE_PLATE_LEDGE_MM,
            ),
            "The plate rim must be the same width on every side",
        )
        require_meets(
            (outer - CASE_PLATE_REBATE_MM[axis]) / 2.0,
            CASE_WALL_MM,
            "Case wall outboard of the plate rebate is too thin",
        )
    centre = (0.0, TILE_PLATE_CENTER_Y_MM)
    pilot_margin = PCB_SUPPORT_PILOT_DIAMETER_MM / 2.0 + FDM_MIN_FEATURE_MM
    head_margin = TILE_PLATE_SCREW_HEAD_DIAMETER_MM / 2.0 + FDM_MIN_FEATURE_MM
    for screw in TILE_PLATE_SCREW_POSITIONS_MM:
        require_meets(
            _outside(screw, centre, PCB_POCKET_SIZE_MM),
            pilot_margin,
            "A tile plate screw pilot breaks into the PCB pocket",
        )
        require_meets(
            -_outside(screw, centre, TILE_PLATE_SIZE_MM[:2]),
            head_margin,
            "A tile plate screw head is too close to the plate edge",
        )
    require(
        len(set(TILE_PLATE_SCREW_POSITIONS_MM)) == len(TILE_PLATE_SCREW_POSITIONS_MM),
        "Tile plate screw positions must be unique",
    )


def validate_buttons() -> None:
    """Button stems stand proud of the bezel; housings clear the plate."""
    protrusion = (
        PCB_TOP_Z_MM
        + PANEL_BUTTON_HEIGHT_MM
        - (CASE_HEIGHT_MM - PANEL_SURFACE_RECESS_MM)
    )
    require_between(
        protrusion,
        PANEL_BUTTON_MIN_PROTRUSION_MM,
        PANEL_BUTTON_MAX_PROTRUSION_MM,
        f"Button stems stand {protrusion:g} mm proud of the bezel",
    )
    require_meets(
        PCB_TO_PLATE_GAP_MM + PANEL_BUTTON_RELIEF_DEPTH_MM - PANEL_BUTTON_BODY_MM[2],
        FDM_MIN_FIT_CLEARANCE_MM,
        "A button housing would touch the plate",
    )
    require_meets(
        TILE_PLATE_THICKNESS_MM
        - PANEL_SURFACE_RECESS_MM
        - PANEL_BUTTON_RELIEF_DEPTH_MM,
        FDM_MIN_FLOOR_MM,
        "Button relief leaves too thin a bezel",
    )
    require_meets(
        (PANEL_BUTTON_HOLE_DIAMETER_MM - PANEL_BUTTON_ACTUATOR_DIAMETER_MM) / 2.0,
        FDM_MIN_FIT_CLEARANCE_MM,
        "Button hole does not clear the stem",
    )
    require_meets(
        (PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM - PANEL_BUTTON_ACTUATOR_DIAMETER_MM) / 2,
        FDM_MIN_FIT_CLEARANCE_MM,
        "Button cap socket does not clear the stem",
    )
    stem_top = PCB_TOP_Z_MM + PANEL_BUTTON_HEIGHT_MM
    require(
        PANEL_BUTTON_CAP_BOTTOM_Z_MM < stem_top <= PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM,
        "Button cap socket must engage the stem",
    )
    require_meets(
        PANEL_BUTTON_CAP_BOTTOM_Z_MM
        + PANEL_BUTTON_CAP_SIZE_MM[2]
        - PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM,
        FDM_MIN_FLOOR_MM,
        "Button cap socket leaves too thin a roof",
    )
    relief = max(PANEL_BUTTON_BODY_MM[:2]) + 2.0 * PANEL_BUTTON_RELIEF_CLEARANCE_MM
    positions = [button.position_mm for button in PANEL_BUTTONS]
    for index, (x0, y0) in enumerate(positions):
        for x1, y1 in positions[index + 1 :]:
            require_meets(
                max(abs(x0 - x1), abs(y0 - y1)) - relief,
                FDM_MIN_FEATURE_MM,
                "Neighbouring button reliefs merge",
            )


def validate_rocker() -> None:
    """The snap-in rocker fits its cutout in a wall pocketed to panel thickness."""
    require(
        not any(a < c for a, c in zip(CASE_ROCKER_APERTURE_MM, CASE_ROCKER_CUTOUT_MM)),
        "Rocker aperture is smaller than the panel cutout",
    )
    rear_wall = (CASE_DEPTH_MM - CASE_CAVITY_SIZE_MM[1]) / 2.0
    require(
        FDM_MIN_FEATURE_MM <= CASE_ROCKER_PANEL_THICKNESS_MM < rear_wall,
        "Rocker panel thickness must be printable and inside the wall",
    )
    low, high = CASE_ROCKER_PANEL_RANGE_MM
    require_between(
        CASE_ROCKER_PANEL_THICKNESS_MM,
        low,
        high,
        "Rocker panel is outside the cutout's panel-thickness row",
    )
    require_meets(
        CASE_ROCKER_POCKET_ROOF_MM,
        FDM_MIN_FLOOR_MM,
        "Rocker pocket roof under the PCB ledge is too thin",
    )
    half_z = CASE_ROCKER_APERTURE_MM[1] / 2.0
    bottom, top = CASE_ROCKER_POCKET_Z_MM
    require(
        meets(
            CASE_REAR_APERTURE_CENTER_Z_MM - half_z - bottom,
            CASE_ROCKER_LATCH_MARGIN_MM,
        )
        and meets(
            top - CASE_REAR_APERTURE_CENTER_Z_MM - half_z, CASE_ROCKER_LATCH_MARGIN_MM
        )
        and CASE_FLOOR_MM <= bottom
        and top <= PCB_UNDERSIDE_Z_MM,
        "Rocker wall pocket leaves no room for the snap-in latches",
    )
    cavity_half_x = CASE_CAVITY_SIZE_MM[0] / 2.0
    pockets = (
        (CASE_ROCKER_APERTURE_CENTER_X_MM, CASE_ROCKER_POCKET_WIDTH_MM),
        (CASE_JACK_APERTURE_CENTER_X_MM, CASE_JACK_POCKET_WIDTH_MM),
    )
    for centre, width in pockets:
        require_meets(
            cavity_half_x - abs(centre) - width / 2.0,
            FDM_MIN_FEATURE_MM,
            "A rear wall pocket runs into the side wall",
        )
    require_meets(
        abs(pockets[0][0] - pockets[1][0]) - (pockets[0][1] + pockets[1][1]) / 2.0,
        FDM_MIN_FEATURE_MM,
        "Jack and rocker wall pockets merge",
    )


def validate_jack() -> None:
    """The panel jack's bushing fits its hole and its thread spans the panel."""
    require(
        CASE_JACK_APERTURE_DIAMETER_MM > CASE_JACK_BUSHING_DIAMETER_MM,
        "Jack aperture does not clear the bushing",
    )
    rear_wall = (CASE_DEPTH_MM - CASE_CAVITY_SIZE_MM[1]) / 2.0
    require(
        FDM_MIN_FEATURE_MM <= CASE_JACK_PANEL_THICKNESS_MM <= CASE_JACK_MAX_PANEL_MM
        and CASE_JACK_PANEL_THICKNESS_MM < rear_wall,
        "Jack panel thickness is outside the jack's thread range",
    )
    require_meets(
        CASE_JACK_POCKET_WIDTH_MM / 2.0 - CASE_JACK_FLANGE_DIAMETER_MM / 2.0,
        FDM_MIN_FEATURE_MM,
        "Jack wall pocket does not clear the jack flange",
    )


def validate_bottom_keepouts() -> None:
    """Bay keepouts for the panel parts stay clear of the bosses and the Pi."""
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for name, (x0, x1, y0, y1) in BOTTOM_SIDE_KEEPOUTS_MM.items():
        centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        size = (x1 - x0, y1 - y0)
        for boss in PCB_SUPPORT_POSITIONS_MM:
            require(
                not _outside(boss, centre, size) < boss_radius + FDM_MIN_FEATURE_MM,
                f"The {name} bay keepout reaches a support boss",
            )
        require(
            not _outside(PI_CENTER_MM, centre, size) < max(PI_BOARD_SIZE_MM[:2]),
            f"The {name} bay keepout reaches the Pi",
        )


def validate_sd_slot() -> None:
    """The right-wall slot lines up with the Pi's microSD socket."""
    socket_x, socket_y = pi_on_board_xy(PI_SD_SOCKET_ON_PI_MM)
    require(
        socket_x > PI_CENTER_MM[0],
        "The Pi's microSD end must face the right-wall slot",
    )
    require(
        not abs(CASE_SD_SLOT_CENTER_Y_MM - socket_y) > SD_SLOT_TOLERANCE_MM,
        "The microSD slot is not on the socket",
    )
    reach = CASE_CAVITY_SIZE_MM[0] / 2.0 - (PI_CENTER_MM[0] + PI_BOARD_SIZE_MM[0] / 2.0)
    require(
        0.0 < reach <= PI_CLEARANCE_MM + SD_SLOT_TOLERANCE_MM,
        "The Pi's microSD end must sit just inside the right wall",
    )
    slot_z = (
        CASE_SD_SLOT_CENTER_Z_MM - CASE_SD_SLOT_MM[1] / 2.0,
        CASE_SD_SLOT_CENTER_Z_MM + CASE_SD_SLOT_MM[1] / 2.0,
    )
    bottom, top = CASE_WALL_POCKET_Z_MM
    # Preserved as written: only the bottom bound is enforced when the top also fits.
    require(
        bottom <= slot_z[0] or not slot_z[1] <= top,
        "The microSD slot is outside the wall pocket",
    )
    require(
        FDM_MIN_FEATURE_MM <= CASE_SD_PANEL_THICKNESS_MM,
        "The microSD wall pocket leaves too thin a panel",
    )


def validate_pi_bay() -> None:
    """The hanging Pi stays inside the cavity, clear of every support boss."""
    require(
        not int(PI_ROTATION_DEG) % 90,
        "The Pi placement must be a quarter-turn rotation",
    )
    turned = int(PI_ROTATION_DEG) % 180 == 90
    size = (
        (PI_BOARD_SIZE_MM[1], PI_BOARD_SIZE_MM[0]) if turned else PI_BOARD_SIZE_MM[:2]
    )
    envelope = (size[0] + 2.0 * PI_CLEARANCE_MM, size[1] + 2.0 * PI_CLEARANCE_MM)
    cavity_centre = (0.0, CASE_CENTER_OFFSET_Y_MM)
    for axis in (0, 1):
        reach = abs(PI_CENTER_MM[axis] - cavity_centre[axis]) + envelope[axis] / 2.0
        require(
            not reach > CASE_CAVITY_SIZE_MM[axis] / 2.0,
            "The Pi and its clearance run into the cavity wall",
        )
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss in PCB_SUPPORT_POSITIONS_MM:
        require(
            not _outside(boss, PI_CENTER_MM, envelope) < boss_radius,
            "A support boss stands inside the Pi envelope",
        )
    pins = [pi_header_pin_xy(pin) for pin in range(1, PI_HEADER_PIN_COUNT + 1)]
    require(
        not any(_outside(pin, PI_CENTER_MM, size) > 0.0 for pin in pins),
        "A Pi header pin lands outside the Pi",
    )


def describe(domain: str = "Shared hardware") -> str:
    """Return a compact summary suitable for domain validation commands."""
    return (
        f"{domain} dimensions valid: "
        f"{GRID_COUNT} x {SQUARE_SIZE_MM:g} mm = {PLAYING_SPAN_MM:g} mm playing span; "
        f"case {CASE_WIDTH_MM:g} x {CASE_DEPTH_MM:g} x {CASE_HEIGHT_MM:g} mm "
        f"({CASE_DEPTH_MM / MILLIMETRES_PER_INCH:.1f} in deep); "
        f"plate {TILE_PLATE_SIZE_MM[0]:g} x {TILE_PLATE_SIZE_MM[1]:g} mm; "
        f"board {PCB_SIZE_MM[0]:g} x {PCB_SIZE_MM[1]:g} mm"
    )


def validate_piece_seats() -> None:
    """Keep solid sensor covers and sufficient support around the locating holes."""
    require(
        0 < PIECE_LOCATING_FOOT_HEIGHT_MM < TILE_PLATE_PIECE_SEAT_DEPTH_MM,
        "Piece locating foot must fit inside its seat without bottoming out",
    )
    require(
        0 < TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM < TILE_PLATE_PIECE_SEAT_SIDE_MM,
        "Piece ring channel must retain a positive center island",
    )
    groove_width = (
        TILE_PLATE_PIECE_SEAT_SIDE_MM - TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM
    ) / 2
    foot_width = (PIECE_LOCATING_FOOT_SIDE_MM - PIECE_LOCATING_FOOT_INNER_SIDE_MM) / 2
    require(
        meets(groove_width, FDM_MIN_FEATURE_MM)
        and meets(foot_width, FDM_MIN_FEATURE_MM),
        "Piece ring channel and ring foot need printable widths",
    )
    inner_clearance = (
        PIECE_LOCATING_FOOT_INNER_SIDE_MM - TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM
    ) / 2
    require_between(
        inner_clearance,
        FDM_MIN_FIT_CLEARANCE_MM,
        FDM_MAX_FIT_CLEARANCE_MM,
        "Piece ring foot must clear its center island",
    )
    clearance = (TILE_PLATE_PIECE_SEAT_SIDE_MM - PIECE_LOCATING_FOOT_SIDE_MM) / 2
    require_between(
        clearance,
        FDM_MIN_FIT_CLEARANCE_MM,
        FDM_MAX_FIT_CLEARANCE_MM,
        "Piece locating foot needs printable side clearance",
    )
    floor = (
        TILE_PLATE_THICKNESS_MM
        - TILE_PLATE_DARK_SQUARE_DEPTH_MM
        - TILE_PLATE_PIECE_SEAT_DEPTH_MM
    )
    require_meets(
        floor,
        FDM_MIN_FLOOR_MM,
        "Piece seat would break its solid floor above the sensor",
    )
    wall = (TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM - TILE_PLATE_PIECE_SEAT_SIDE_MM) / 2
    require_meets(
        wall, FDM_MIN_FEATURE_MM, "Piece seat needs a reinforced underside wall"
    )
    require(
        TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM < TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM,
        "Piece seat support must fit within its square pocket",
    )
    half_support = TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM / 2
    for square in BOARD_SQUARES:
        dx = max(
            abs(square.led_position_mm[0] - square.centre_mm[0])
            - TILE_PLATE_LED_POCKET_MM[0] / 2,
            0,
        )
        dy = max(
            abs(square.led_position_mm[1] - square.centre_mm[1])
            - TILE_PLATE_LED_POCKET_MM[1] / 2,
            0,
        )
        require(
            not (dx <= half_support and dy <= half_support),
            "Piece seat support overlaps the LED pocket",
        )
