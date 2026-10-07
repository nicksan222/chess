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
        if (
            not COMPACT_BOARD_MIN_SPAN_MM
            <= span - 2 * CASE_FRAME_WIDTH_MM
            <= COMPACT_BOARD_MAX_SPAN_MM
        ):
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
    if PI_BAY_HEIGHT_MM < PI_BOARD_TO_BOARD_MM + PI_BOARD_SIZE_MM[2] + PI_CLEARANCE_MM:
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
        raise ValueError("LED pocket must retain a roof around the open window")
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

    validate_board_pocket()
    validate_plate_rim()
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
        for led_x, led_y in (square.led_position_mm for square in BOARD_SQUARES):
            gap = max(abs(boss_x - led_x), abs(boss_y - led_y))
            if gap < boss_radius + TILE_PLATE_LED_POCKET_MM[0] / 2.0:
                raise ValueError("A support boss collides with an LED position")
        for sensor_x, sensor_y in (square.hall_position_mm for square in BOARD_SQUARES):
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
        if not (strip_min_y <= y - half_y and y + half_y <= strip_max_y):
            raise ValueError(f"Control panel {name} extends off the control strip")
        if abs(x) + half_x > PLAYING_SPAN_MM / 2.0:
            raise ValueError(f"Control panel {name} extends off the board")
    if len(PANEL_BUTTONS) != PANEL_BUTTON_COUNT:
        raise ValueError("Control panel must place every button")
    if len({button.position_mm for button in PANEL_BUTTONS}) != PANEL_BUTTON_COUNT:
        raise ValueError("Button positions must be unique")
    if PANEL_OLED_BEZEL_CLEARANCE_XY_MM <= 0.0:
        raise ValueError("Display recess must include positive XY assembly clearance")
    if any(
        recess <= module
        for recess, module in zip(PANEL_OLED_BEZEL_INNER_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display recess must be larger than the module")
    if any(
        window >= module
        for window, module in zip(PANEL_OLED_SCREEN_SIZE_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display window must be smaller than the module behind it")

    for aperture, emitter, pocket in zip(
        TILE_PLATE_LED_WINDOW_MM, LED_EMITTER_WINDOW_MM, TILE_PLATE_LED_POCKET_MM[:2]
    ):
        if aperture < emitter + LED_PACKAGE_TOLERANCE_MM:
            raise ValueError("LED window must expose the whole emitter")
        if not meets((pocket - aperture) / 2, FDM_MIN_FEATURE_MM):
            raise ValueError("LED window must retain a printable surrounding roof")

    if not 0 < PANEL_SURFACE_RECESS_MM < TILE_PLATE_THICKNESS_MM:
        raise ValueError("Control surface must be recessed within the plate")
    screw_tip = (
        PANEL_OLED_PCB_BOTTOM_Z_MM
        + PANEL_OLED_PCB_THICKNESS_MM
        - PANEL_OLED_SCREW_LENGTH_MM
    )
    if not meets(
        screw_tip - (PANEL_OLED_LEDGE_BOTTOM_Z_MM + PANEL_OLED_PILOT_FLOOR_MM),
        FDM_MIN_FIT_CLEARANCE_MM,
    ):
        raise ValueError("Display screw would bottom out in its blind pilot")
    if not meets(
        (PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM - PANEL_OLED_SCREW_HEAD_DIAMETER_MM)
        / 2,
        FDM_MIN_FIT_CLEARANCE_MM,
    ):
        raise ValueError("Display access must clear the screw head")
    if (
        PANEL_OLED_PCB_BOTTOM_Z_MM
        + PANEL_OLED_PCB_THICKNESS_MM
        + PANEL_OLED_SCREW_HEAD_HEIGHT_MM
        > PANEL_OLED_SCREEN_Z_MM + 0.1
    ):
        raise ValueError("Display screw head does not fit below the bezel roof")
    for dx, dy in PANEL_OLED_MOUNT_HOLES_MM:
        for center, span in zip((dx, dy), PANEL_OLED_BEZEL_OUTER_MM):
            if not meets(
                span / 2 - abs(center) - PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM / 2,
                FDM_MIN_FEATURE_MM,
            ):
                raise ValueError("Display access hole leaves too thin a bezel edge")
    if not meets(
        (PANEL_OLED_LEDGE_WIDTH_MM - PANEL_OLED_PILOT_DIAMETER_MM) / 2,
        FDM_MIN_FEATURE_MM,
    ):
        raise ValueError("Display mounting pilot needs printable surrounding walls")
    if (
        PANEL_OLED_PCB_BOTTOM_Z_MM - PANEL_OLED_LEDGE_BOTTOM_Z_MM
        <= PANEL_OLED_PILOT_FLOOR_MM
    ):
        raise ValueError("Display mounting pilot needs depth above its floor")
    if not meets(PANEL_OLED_PILOT_FLOOR_MM, FDM_MIN_FLOOR_MM):
        raise ValueError("Display mounting pilot must retain a printable floor")
    if not meets(PANEL_OLED_BEZEL_WALL_MM, FDM_MIN_FEATURE_MM) or not meets(
        PANEL_OLED_BEZEL_ROOF_MM, FDM_MIN_FEATURE_MM
    ):
        raise ValueError("Display bezel needs printable walls and roof")
    if any(
        wire >= body
        for wire, body in zip(PANEL_OLED_WIRE_OPENING_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display wire opening must leave supporting material")
    validate_piece_seats()
    validate_buttons()
    validate_rocker()
    validate_jack()
    validate_pi_bay()
    validate_bottom_keepouts()
    validate_sd_slot()
    if len(EXPANDER_POSITIONS_BY_BANK_MM) != 8:
        raise ValueError("Board composition must place eight GPIO expanders")
    if len(set(EXPANDER_POSITIONS_BY_BANK_MM.values())) != 8:
        raise ValueError("GPIO expander positions must be unique")

    BOARD_SQUARES.validate_topology()

    if not isclose(PCB_SIZE_MM[0], PLAYING_SPAN_MM):
        raise ValueError("Board must be exactly as wide as the playing area")
    if not isclose(PCB_SIZE_MM[1], PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM):
        raise ValueError("Board must carry the playing area and the control strip")

    for part_size in PRINTED_PART_SIZES_MM:
        if not fits_build_volume(part_size, REFERENCE_SERVICE_BUILD_VOLUME_MM):
            raise ValueError(
                "A printed part exceeds the print-service reference volume"
            )


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
    if (
        not FDM_MIN_FIT_CLEARANCE_MM
        <= PCB_POCKET_CLEARANCE_MM
        <= FDM_MAX_FIT_CLEARANCE_MM
    ):
        raise ValueError("PCB pocket clearance is outside the prototype fit range")
    if not isclose(PCB_CENTER_OFFSET_Y_MM, CASE_CENTER_OFFSET_Y_MM):
        raise ValueError("The PCB pocket must be centred on the board")
    for axis, outer in enumerate((CASE_WIDTH_MM, CASE_DEPTH_MM)):
        if not isclose(
            PCB_POCKET_SIZE_MM[axis], PCB_SIZE_MM[axis] + 2.0 * PCB_POCKET_CLEARANCE_MM
        ):
            raise ValueError("PCB pocket must be the board outline plus clearance")
        if not meets((outer - PCB_POCKET_SIZE_MM[axis]) / 2.0, CASE_WALL_MM):
            raise ValueError("Case wall outboard of the PCB pocket is too thin")
        # The board can float by the clearance; with it pushed fully away from a
        # side, the ledge on that side must still carry it.
        for side in (-1.0, 1.0):
            board_edge = side * PCB_SIZE_MM[axis] / 2.0
            cavity_edge = side * CASE_CAVITY_SIZE_MM[axis] / 2.0
            bearing = side * (board_edge - cavity_edge) - PCB_POCKET_CLEARANCE_MM
            if not meets(bearing, FDM_MIN_FEATURE_MM):
                raise ValueError("The PCB ledge does not support every board edge")
    if not meets(
        PCB_BOTTOM_EDGE_KEEPOUT_MM, CASE_PCB_LEDGE_OVERLAP_MM + PCB_POCKET_CLEARANCE_MM
    ):
        raise ValueError("The PCB ledge reaches past the bottom-side edge keepout")
    cavity_centre = (0.0, CASE_CENTER_OFFSET_Y_MM)
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss in PCB_SUPPORT_POSITIONS_MM:
        if _outside(boss, cavity_centre, CASE_CAVITY_SIZE_MM) > -boss_radius:
            raise ValueError("A support boss is not inside the cavity under the board")


def validate_plate_rim() -> None:
    """The plate rests on a rim outboard of the PCB pocket, held by screws there."""
    if not isclose(TILE_PLATE_CENTER_Y_MM, CASE_CENTER_OFFSET_Y_MM):
        raise ValueError("The plate must be centred on the case")
    for axis, outer in enumerate((CASE_WIDTH_MM, CASE_DEPTH_MM)):
        if not isclose(
            CASE_PLATE_REBATE_MM[axis],
            TILE_PLATE_SIZE_MM[axis] + TILE_PLATE_CLEARANCE_MM,
        ):
            raise ValueError("The plate rebate must be the plate plus its clearance")
        if not isclose(
            (TILE_PLATE_SIZE_MM[axis] - PCB_POCKET_SIZE_MM[axis]) / 2.0,
            CASE_PLATE_LEDGE_MM,
        ):
            raise ValueError("The plate rim must be the same width on every side")
        if not meets((outer - CASE_PLATE_REBATE_MM[axis]) / 2.0, CASE_WALL_MM):
            raise ValueError("Case wall outboard of the plate rebate is too thin")
    centre = (0.0, TILE_PLATE_CENTER_Y_MM)
    pilot_margin = PCB_SUPPORT_PILOT_DIAMETER_MM / 2.0 + FDM_MIN_FEATURE_MM
    head_margin = TILE_PLATE_SCREW_HEAD_DIAMETER_MM / 2.0 + FDM_MIN_FEATURE_MM
    for screw in TILE_PLATE_SCREW_POSITIONS_MM:
        if not meets(_outside(screw, centre, PCB_POCKET_SIZE_MM), pilot_margin):
            raise ValueError("A tile plate screw pilot breaks into the PCB pocket")
        if not meets(-_outside(screw, centre, TILE_PLATE_SIZE_MM[:2]), head_margin):
            raise ValueError("A tile plate screw head is too close to the plate edge")
    if len(set(TILE_PLATE_SCREW_POSITIONS_MM)) != len(TILE_PLATE_SCREW_POSITIONS_MM):
        raise ValueError("Tile plate screw positions must be unique")


def validate_buttons() -> None:
    """Button stems stand proud of the bezel; housings clear the plate."""
    protrusion = (
        PCB_TOP_Z_MM
        + PANEL_BUTTON_HEIGHT_MM
        - (CASE_HEIGHT_MM - PANEL_SURFACE_RECESS_MM)
    )
    if (
        not PANEL_BUTTON_MIN_PROTRUSION_MM
        <= protrusion
        <= PANEL_BUTTON_MAX_PROTRUSION_MM
    ):
        raise ValueError(f"Button stems stand {protrusion:g} mm proud of the bezel")
    if not meets(
        PCB_TO_PLATE_GAP_MM + PANEL_BUTTON_RELIEF_DEPTH_MM - PANEL_BUTTON_BODY_MM[2],
        FDM_MIN_FIT_CLEARANCE_MM,
    ):
        raise ValueError("A button housing would touch the plate")
    if not meets(
        TILE_PLATE_THICKNESS_MM
        - PANEL_SURFACE_RECESS_MM
        - PANEL_BUTTON_RELIEF_DEPTH_MM,
        FDM_MIN_FLOOR_MM,
    ):
        raise ValueError("Button relief leaves too thin a bezel")
    if not meets(
        (PANEL_BUTTON_HOLE_DIAMETER_MM - PANEL_BUTTON_ACTUATOR_DIAMETER_MM) / 2.0,
        FDM_MIN_FIT_CLEARANCE_MM,
    ):
        raise ValueError("Button hole does not clear the stem")
    if not meets(
        (PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM - PANEL_BUTTON_ACTUATOR_DIAMETER_MM) / 2,
        FDM_MIN_FIT_CLEARANCE_MM,
    ):
        raise ValueError("Button cap socket does not clear the stem")
    stem_top = PCB_TOP_Z_MM + PANEL_BUTTON_HEIGHT_MM
    if not PANEL_BUTTON_CAP_BOTTOM_Z_MM < stem_top <= PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM:
        raise ValueError("Button cap socket must engage the stem")
    if not meets(
        PANEL_BUTTON_CAP_BOTTOM_Z_MM
        + PANEL_BUTTON_CAP_SIZE_MM[2]
        - PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM,
        FDM_MIN_FLOOR_MM,
    ):
        raise ValueError("Button cap socket leaves too thin a roof")
    relief = max(PANEL_BUTTON_BODY_MM[:2]) + 2.0 * PANEL_BUTTON_RELIEF_CLEARANCE_MM
    positions = [button.position_mm for button in PANEL_BUTTONS]
    for index, (x0, y0) in enumerate(positions):
        for x1, y1 in positions[index + 1 :]:
            if not meets(max(abs(x0 - x1), abs(y0 - y1)) - relief, FDM_MIN_FEATURE_MM):
                raise ValueError("Neighbouring button reliefs merge")


def validate_rocker() -> None:
    """The snap-in rocker fits its cutout in a wall pocketed to panel thickness."""
    if any(a < c for a, c in zip(CASE_ROCKER_APERTURE_MM, CASE_ROCKER_CUTOUT_MM)):
        raise ValueError("Rocker aperture is smaller than the panel cutout")
    rear_wall = (CASE_DEPTH_MM - CASE_CAVITY_SIZE_MM[1]) / 2.0
    if not FDM_MIN_FEATURE_MM <= CASE_ROCKER_PANEL_THICKNESS_MM < rear_wall:
        raise ValueError("Rocker panel thickness must be printable and inside the wall")
    low, high = CASE_ROCKER_PANEL_RANGE_MM
    if not low <= CASE_ROCKER_PANEL_THICKNESS_MM <= high:
        raise ValueError("Rocker panel is outside the cutout's panel-thickness row")
    if not meets(CASE_ROCKER_POCKET_ROOF_MM, FDM_MIN_FLOOR_MM):
        raise ValueError("Rocker pocket roof under the PCB ledge is too thin")
    half_z = CASE_ROCKER_APERTURE_MM[1] / 2.0
    bottom, top = CASE_ROCKER_POCKET_Z_MM
    if not (
        meets(
            CASE_REAR_APERTURE_CENTER_Z_MM - half_z - bottom,
            CASE_ROCKER_LATCH_MARGIN_MM,
        )
        and meets(
            top - CASE_REAR_APERTURE_CENTER_Z_MM - half_z, CASE_ROCKER_LATCH_MARGIN_MM
        )
        and CASE_FLOOR_MM <= bottom
        and top <= PCB_UNDERSIDE_Z_MM
    ):
        raise ValueError("Rocker wall pocket leaves no room for the snap-in latches")
    cavity_half_x = CASE_CAVITY_SIZE_MM[0] / 2.0
    pockets = (
        (CASE_ROCKER_APERTURE_CENTER_X_MM, CASE_ROCKER_POCKET_WIDTH_MM),
        (CASE_JACK_APERTURE_CENTER_X_MM, CASE_JACK_POCKET_WIDTH_MM),
    )
    for centre, width in pockets:
        if not meets(cavity_half_x - abs(centre) - width / 2.0, FDM_MIN_FEATURE_MM):
            raise ValueError("A rear wall pocket runs into the side wall")
    if not meets(
        abs(pockets[0][0] - pockets[1][0]) - (pockets[0][1] + pockets[1][1]) / 2.0,
        FDM_MIN_FEATURE_MM,
    ):
        raise ValueError("Jack and rocker wall pockets merge")


def validate_jack() -> None:
    """The panel jack's bushing fits its hole and its thread spans the panel."""
    if CASE_JACK_APERTURE_DIAMETER_MM <= CASE_JACK_BUSHING_DIAMETER_MM:
        raise ValueError("Jack aperture does not clear the bushing")
    rear_wall = (CASE_DEPTH_MM - CASE_CAVITY_SIZE_MM[1]) / 2.0
    if not (
        FDM_MIN_FEATURE_MM <= CASE_JACK_PANEL_THICKNESS_MM <= CASE_JACK_MAX_PANEL_MM
        and CASE_JACK_PANEL_THICKNESS_MM < rear_wall
    ):
        raise ValueError("Jack panel thickness is outside the jack's thread range")
    if not meets(
        CASE_JACK_POCKET_WIDTH_MM / 2.0 - CASE_JACK_FLANGE_DIAMETER_MM / 2.0,
        FDM_MIN_FEATURE_MM,
    ):
        raise ValueError("Jack wall pocket does not clear the jack flange")


def validate_bottom_keepouts() -> None:
    """Bay keepouts for the panel parts stay clear of the bosses and the Pi."""
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for name, (x0, x1, y0, y1) in BOTTOM_SIDE_KEEPOUTS_MM.items():
        centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        size = (x1 - x0, y1 - y0)
        for boss in PCB_SUPPORT_POSITIONS_MM:
            if _outside(boss, centre, size) < boss_radius + FDM_MIN_FEATURE_MM:
                raise ValueError(f"The {name} bay keepout reaches a support boss")
        if _outside(PI_CENTER_MM, centre, size) < max(PI_BOARD_SIZE_MM[:2]):
            raise ValueError(f"The {name} bay keepout reaches the Pi")


def validate_sd_slot() -> None:
    """The right-wall slot lines up with the Pi's microSD socket."""
    socket_x, socket_y = pi_on_board_xy(PI_SD_SOCKET_ON_PI_MM)
    if socket_x <= PI_CENTER_MM[0]:
        raise ValueError("The Pi's microSD end must face the right-wall slot")
    if abs(CASE_SD_SLOT_CENTER_Y_MM - socket_y) > 1e-9:
        raise ValueError("The microSD slot is not on the socket")
    reach = CASE_CAVITY_SIZE_MM[0] / 2.0 - (PI_CENTER_MM[0] + PI_BOARD_SIZE_MM[0] / 2.0)
    if not 0.0 < reach <= PI_CLEARANCE_MM + 1e-9:
        raise ValueError("The Pi's microSD end must sit just inside the right wall")
    slot_z = (
        CASE_SD_SLOT_CENTER_Z_MM - CASE_SD_SLOT_MM[1] / 2.0,
        CASE_SD_SLOT_CENTER_Z_MM + CASE_SD_SLOT_MM[1] / 2.0,
    )
    bottom, top = CASE_WALL_POCKET_Z_MM
    if not bottom <= slot_z[0] and slot_z[1] <= top:
        raise ValueError("The microSD slot is outside the wall pocket")
    if not FDM_MIN_FEATURE_MM <= CASE_SD_PANEL_THICKNESS_MM:
        raise ValueError("The microSD wall pocket leaves too thin a panel")


def validate_pi_bay() -> None:
    """The hanging Pi stays inside the cavity, clear of every support boss."""
    if int(PI_ROTATION_DEG) % 90:
        raise ValueError("The Pi placement must be a quarter-turn rotation")
    turned = int(PI_ROTATION_DEG) % 180 == 90
    size = (
        (PI_BOARD_SIZE_MM[1], PI_BOARD_SIZE_MM[0]) if turned else PI_BOARD_SIZE_MM[:2]
    )
    envelope = (size[0] + 2.0 * PI_CLEARANCE_MM, size[1] + 2.0 * PI_CLEARANCE_MM)
    cavity_centre = (0.0, CASE_CENTER_OFFSET_Y_MM)
    for axis in (0, 1):
        reach = abs(PI_CENTER_MM[axis] - cavity_centre[axis]) + envelope[axis] / 2.0
        if reach > CASE_CAVITY_SIZE_MM[axis] / 2.0:
            raise ValueError("The Pi and its clearance run into the cavity wall")
    boss_radius = PCB_SUPPORT_BOSS_DIAMETER_MM / 2.0
    for boss in PCB_SUPPORT_POSITIONS_MM:
        if _outside(boss, PI_CENTER_MM, envelope) < boss_radius:
            raise ValueError("A support boss stands inside the Pi envelope")
    pins = [pi_header_pin_xy(pin) for pin in range(1, PI_HEADER_PIN_COUNT + 1)]
    if any(_outside(pin, PI_CENTER_MM, size) > 0.0 for pin in pins):
        raise ValueError("A Pi header pin lands outside the Pi")


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
    if not 0 < PIECE_LOCATING_FOOT_HEIGHT_MM < TILE_PLATE_PIECE_SEAT_DEPTH_MM:
        raise ValueError(
            "Piece locating foot must fit inside its seat without bottoming out"
        )
    if not 0 < TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM < TILE_PLATE_PIECE_SEAT_SIDE_MM:
        raise ValueError("Piece ring channel must retain a positive center island")
    groove_width = (
        TILE_PLATE_PIECE_SEAT_SIDE_MM - TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM
    ) / 2
    foot_width = (PIECE_LOCATING_FOOT_SIDE_MM - PIECE_LOCATING_FOOT_INNER_SIDE_MM) / 2
    if not meets(groove_width, FDM_MIN_FEATURE_MM) or not meets(
        foot_width, FDM_MIN_FEATURE_MM
    ):
        raise ValueError("Piece ring channel and ring foot need printable widths")
    inner_clearance = (
        PIECE_LOCATING_FOOT_INNER_SIDE_MM - TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM
    ) / 2
    if not FDM_MIN_FIT_CLEARANCE_MM <= inner_clearance <= FDM_MAX_FIT_CLEARANCE_MM:
        raise ValueError("Piece ring foot must clear its center island")
    clearance = (TILE_PLATE_PIECE_SEAT_SIDE_MM - PIECE_LOCATING_FOOT_SIDE_MM) / 2
    if not FDM_MIN_FIT_CLEARANCE_MM <= clearance <= FDM_MAX_FIT_CLEARANCE_MM:
        raise ValueError("Piece locating foot needs printable side clearance")
    floor = (
        TILE_PLATE_THICKNESS_MM
        - TILE_PLATE_DARK_SQUARE_DEPTH_MM
        - TILE_PLATE_PIECE_SEAT_DEPTH_MM
    )
    if not meets(floor, FDM_MIN_FLOOR_MM):
        raise ValueError("Piece seat would break its solid floor above the sensor")
    wall = (TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM - TILE_PLATE_PIECE_SEAT_SIDE_MM) / 2
    if not meets(wall, FDM_MIN_FEATURE_MM):
        raise ValueError("Piece seat needs a reinforced underside wall")
    if TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM >= TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM:
        raise ValueError("Piece seat support must fit within its square pocket")
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
        if dx <= half_support and dy <= half_support:
            raise ValueError("Piece seat support overlaps the LED pocket")
