"""Cross-part physical validation and dimension summaries."""

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
    PCB_SIZE_MM,
    PCB_THICKNESS_MM,
    PLAYING_SPAN_MM,
    SQUARE_SIZE_MM,
)
from .case import (
    CASE_DEPTH_MM,
    CASE_FLOOR_MM,
    CASE_FRAME_WIDTH_MM,
    CASE_HEIGHT_MM,
    CASE_PLATE_LEDGE_MM,
    CASE_WALL_MM,
    CASE_WIDTH_MM,
    PCB_SUPPORT_BOSS_DIAMETER_MM,
    PCB_SUPPORT_PILOT_DEPTH_MM,
    PCB_SUPPORT_PILOT_DIAMETER_MM,
    PCB_SUPPORT_POSITIONS_MM,
    PCB_TO_PLATE_GAP_MM,
    PI_BAY_HEIGHT_MM,
    PI_BOARD_SIZE_MM,
    PI_CLEARANCE_MM,
    PI_HEADER_HEIGHT_MM,
)
from .panel import (
    PANEL_BUTTON_COUNT,
    PANEL_BUTTON_HOLE_DIAMETER_MM,
    PANEL_OLED_CENTER_MM,
    PANEL_OLED_MODULE_MM,
    PANEL_OLED_RECESS_CLEARANCE_XY_MM,
    PANEL_OLED_RECESS_MM,
    PANEL_OLED_WINDOW_MM,
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
    TILE_PLATE_CLEARANCE_MM,
    TILE_PLATE_DARK_SQUARE_DEPTH_MM,
    TILE_PLATE_DIFFUSER_SKIN_MM,
    TILE_PLATE_GROOVE_WIDTH_MM,
    TILE_PLATE_LED_POCKET_MM,
    TILE_PLATE_RIB_WIDTH_MM,
    TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM,
    TILE_PLATE_SCREW_HEAD_DEPTH_MM,
    TILE_PLATE_SCREW_HEAD_DIAMETER_MM,
    TILE_PLATE_SCREW_POSITIONS_MM,
    TILE_PLATE_SPAN_MM,
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
            PANEL_OLED_RECESS_MM[0] / 2.0,
            PANEL_OLED_RECESS_MM[1] / 2.0,
        ),
    )
    for name, x, y, half_x, half_y in panel_features:
        if not strip_min_y <= y - half_y and y + half_y <= strip_max_y:
            raise ValueError(f"Control panel {name} extends off the control strip")
        if abs(x) + half_x > PLAYING_SPAN_MM / 2.0:
            raise ValueError(f"Control panel {name} extends off the board")
    if len(PANEL_BUTTONS) != PANEL_BUTTON_COUNT:
        raise ValueError("Control panel must place every button")
    if len({button.position_mm for button in PANEL_BUTTONS}) != PANEL_BUTTON_COUNT:
        raise ValueError("Button positions must be unique")
    if PANEL_OLED_RECESS_CLEARANCE_XY_MM <= 0.0:
        raise ValueError("Display recess must include positive XY assembly clearance")
    if any(
        recess <= module
        for recess, module in zip(PANEL_OLED_RECESS_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display recess must be larger than the module")
    if any(
        window >= module
        for window, module in zip(PANEL_OLED_WINDOW_MM, PANEL_OLED_MODULE_MM[:2])
    ):
        raise ValueError("Display window must be smaller than the module behind it")

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
