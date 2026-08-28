"""Authoritative millimetre dimensions and physical guardrails for Chess CAD."""

from math import isclose


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
COMPACT_BOARD_MAX_HEIGHT_MM = 30.0
COMPACT_TILE_MIN_HEIGHT_MM = 5.0
COMPACT_TILE_MAX_HEIGHT_MM = 15.0
FIDE_REFERENCE_SQUARE_MIN_MM = 50.0
FIDE_REFERENCE_SQUARE_MAX_MM = 60.0

# Prototype FDM guardrails. These catch implausible geometry, but do not replace
# printer-, material-, and orientation-specific slicer validation.
REFERENCE_COMPACT_BUILD_VOLUME_MM = (180.0, 210.0, 220.0)
REFERENCE_LARGE_BUILD_VOLUME_MM = (360.0, 360.0, 360.0)
PRINT_BED_EDGE_MARGIN_MM = 5.0
FDM_REFERENCE_NOZZLE_MM = 0.4
FDM_MIN_FEATURE_MM = 2.0 * FDM_REFERENCE_NOZZLE_MM
FDM_MIN_FLOOR_MM = 1.0
FDM_MIN_FIT_CLEARANCE_MM = 0.2
FDM_MAX_FIT_CLEARANCE_MM = 0.5

# Board grid.
GRID_COUNT = 8
SQUARE_SIZE_MM = 40.0
TILE_EDGE_CLEARANCE_MM = 0.4
TILE_EDGE_CLEARANCE_PER_SIDE_MM = TILE_EDGE_CLEARANCE_MM / 2.0
TILE_SIZE_MM = SQUARE_SIZE_MM - TILE_EDGE_CLEARANCE_MM
PLAYING_SPAN_MM = SQUARE_SIZE_MM * GRID_COUNT

# Universal tile enclosure.
TILE_HEIGHT_MM = 8.5
TILE_BOTTOM_HEIGHT_MM = 5.6
TILE_TOP_THICKNESS_MM = TILE_HEIGHT_MM - TILE_BOTTOM_HEIGHT_MM
TILE_OUTER_RADIUS_MM = 1.2

# WS2812B-compatible 5050 addressable RGB LED reference. The Worldsemi
# mechanical drawing specifies 5.0 x 5.4 x 1.57 mm with 0.05 mm default
# tolerance; Adafruit independently identifies the package as a 5 mm square.
# https://www.ledyilighting.com/wp-content/uploads/2025/02/WS2812B-datasheet.pdf
# https://www.adafruit.com/product/1655
LED_PACKAGE_REFERENCE = "WS2812B-compatible 5050 RGB"
LED_PACKAGE_NOMINAL_SIZE_MM = (5.4, 5.0, 1.57)
LED_PACKAGE_TOLERANCE_MM = 0.05
LED_PACKAGE_MAX_SIZE_MM = tuple(
    axis + LED_PACKAGE_TOLERANCE_MM for axis in LED_PACKAGE_NOMINAL_SIZE_MM
)
LED_PACKAGE_CLEARANCE_PER_SIDE_MM = 0.2
LED_PACKAGE_VERTICAL_CLEARANCE_MM = 0.2
LED_EMITTER_WINDOW_MM = (4.0, 4.0)
LED_POSITION_MM = (13.0, 13.0)
LED_POCKET_MM = (6.2, 6.2, 1.85)
LED_APERTURE_MM = (4.2, 4.2)
LED_BREAKOUT_PCB_MM = (9.0, 9.0, 0.8)

# A miniature glass reed switch reference for the wired-tile presentation.
# Final sensitivity/ampere-turn selection remains an electronics prototype task.
REED_SENSOR_BODY_MM = (14.0, 2.2)
REED_SENSOR_POSITION_MM = (0.0, 0.0)
ELECTRONICS_WIRE_DIAMETER_MM = 0.8

MAGNET_RING_OUTER_DIAMETER_MM = 26.0
MAGNET_RING_INNER_DIAMETER_MM = 20.0
MAGNET_RING_DEPTH_MM = 1.5

TILE_BOTTOM_FLOOR_MM = 1.3
TILE_BOTTOM_WALL_MM = 2.0
TILE_WIRE_PORT_WIDTH_MM = 4.8
TILE_WIRE_PORT_HEIGHT_MM = 2.6
TILE_WIRE_PORT_CENTER_Z_MM = 3.0
TILE_WIRE_PORT_CUTTER_DEPTH_MM = 4.0
TILE_LID_CLEARANCE_MM = 0.2
TILE_LID_REBATE_EDGE_MM = 0.9
TILE_LID_REBATE_HEIGHT_MM = 1.2
TILE_LID_RAIL_DEPTH_MM = 0.95
TILE_LID_RAIL_WIDTH_MM = 1.0
TILE_LID_RAIL_OVERLAP_MM = 0.05
TILE_BOOLEAN_RECESS_OVERLAP_MM = 0.2
TILE_BOOLEAN_THROUGH_OVERLAP_MM = 0.4
TILE_WIRE_PORT_CUTTER_OVERLAP_MM = 1.5

# Simple wooden-board mounting. Four shallow underside pockets locate standard
# adhesive-backed hook-and-loop squares. Two reinforced holes provide an
# optional direct-to-wood screw attachment without requiring another print.
TILE_VELCRO_PAD_SIZE_MM = (9.0, 9.0)
TILE_VELCRO_PAD_DEPTH_MM = 0.25
TILE_VELCRO_PAD_RADIUS_MM = 1.3
TILE_VELCRO_PAD_POSITIONS_MM = (
    (-12.5, -12.5),
    (12.5, -12.5),
    (-12.5, 12.5),
    (12.5, 12.5),
)
TILE_MOUNT_SCREW_POSITIONS_MM = ((-9.0, 0.0), (9.0, 0.0))
TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM = 3.4
TILE_MOUNT_SCREW_HEAD_DIAMETER_MM = 6.8
TILE_MOUNT_SCREW_HEAD_DEPTH_MM = 1.6
TILE_MOUNT_SCREW_BOSS_DIAMETER_MM = 9.0
TILE_MOUNT_SCREW_BOSS_HEIGHT_MM = 2.8

TILE_INTERNAL_CAVITY_SIZE_MM = TILE_SIZE_MM - 2.0 * TILE_BOTTOM_WALL_MM
TILE_LID_RAIL_OUTER_SPAN_MM = TILE_SIZE_MM - 2.0 * (
    TILE_BOTTOM_WALL_MM - TILE_LID_CLEARANCE_MM
)
TILE_LID_RAIL_INNER_SPAN_MM = (
    TILE_LID_RAIL_OUTER_SPAN_MM - 2.0 * TILE_LID_RAIL_WIDTH_MM
)
TILE_LID_REBATE_CENTER_Z_MM = (
    TILE_BOTTOM_HEIGHT_MM
    + TILE_BOOLEAN_RECESS_OVERLAP_MM
    - TILE_LID_REBATE_HEIGHT_MM / 2.0
)
TILE_WIRE_PORT_CUTTER_OFFSET_MM = (
    TILE_SIZE_MM / 2.0
    + TILE_WIRE_PORT_CUTTER_OVERLAP_MM
    - TILE_WIRE_PORT_CUTTER_DEPTH_MM / 2.0
)
TILE_MAGNET_RING_WIDTH_MM = (
    MAGNET_RING_OUTER_DIAMETER_MM - MAGNET_RING_INNER_DIAMETER_MM
) / 2.0
TILE_MAGNET_TOP_SKIN_MM = TILE_TOP_THICKNESS_MM - MAGNET_RING_DEPTH_MM
TILE_LED_TOP_SKIN_MM = TILE_TOP_THICKNESS_MM - LED_POCKET_MM[2]
TILE_TOP_PRINTED_HEIGHT_MM = (
    TILE_TOP_THICKNESS_MM
    + TILE_LID_RAIL_DEPTH_MM
    - TILE_LID_RAIL_OVERLAP_MM
)
TILE_BOTTOM_BASE_SIZE_MM = (
    TILE_SIZE_MM,
    TILE_SIZE_MM,
    TILE_BOTTOM_HEIGHT_MM,
)
TILE_TOP_BASE_SIZE_MM = (
    TILE_SIZE_MM,
    TILE_SIZE_MM,
    TILE_TOP_THICKNESS_MM,
)
TILE_PRINTED_PART_ENVELOPE_MM = (
    TILE_SIZE_MM,
    TILE_SIZE_MM,
    max(TILE_BOTTOM_HEIGHT_MM, TILE_TOP_PRINTED_HEIGHT_MM),
)
TILE_ASSEMBLED_ENVELOPE_MM = (TILE_SIZE_MM, TILE_SIZE_MM, TILE_HEIGHT_MM)

# Empty printable board tray. The tray has no permanent chess squares: the 64
# printable electronic tiles create the finished playing surface. Velcro adheres
# to its flat floor; blind pilot holes support the optional screw attachment.
BOARD_FRAME_WIDTH_MM = 10.0
BOARD_FINISHED_SPAN_MM = PLAYING_SPAN_MM + 2.0 * BOARD_FRAME_WIDTH_MM
BOARD_FLOOR_THICKNESS_MM = 4.0
BOARD_HEIGHT_MM = BOARD_FLOOR_THICKNESS_MM + TILE_HEIGHT_MM
BOARD_TRAY_OUTER_SIZE_MM = (
    BOARD_FINISHED_SPAN_MM,
    BOARD_FINISHED_SPAN_MM,
    BOARD_HEIGHT_MM,
)
BOARD_TRAY_CAVITY_SIZE_MM = (
    PLAYING_SPAN_MM,
    PLAYING_SPAN_MM,
    BOARD_HEIGHT_MM - BOARD_FLOOR_THICKNESS_MM,
)
BOARD_MOUNT_SCREW_PILOT_DIAMETER_MM = 2.5
BOARD_MOUNT_SCREW_PILOT_DEPTH_MM = 3.0
BOARD_LED_POSITIONS_MM = tuple(
    (
        row,
        column,
        -PLAYING_SPAN_MM / 2.0
        + (column + 0.5) * SQUARE_SIZE_MM
        + LED_POSITION_MM[0],
        PLAYING_SPAN_MM / 2.0
        - (row + 0.5) * SQUARE_SIZE_MM
        + LED_POSITION_MM[1],
    )
    for row in range(GRID_COUNT)
    for column in range(GRID_COUNT)
)
BOARD_MOUNT_SCREW_PILOT_POSITIONS_MM = tuple(
    (
        row,
        column,
        screw_index,
        -PLAYING_SPAN_MM / 2.0
        + (column + 0.5) * SQUARE_SIZE_MM
        + local_x,
        PLAYING_SPAN_MM / 2.0
        - (row + 0.5) * SQUARE_SIZE_MM
        + local_y,
    )
    for row in range(GRID_COUNT)
    for column in range(GRID_COUNT)
    for screw_index, (local_x, local_y) in enumerate(
        TILE_MOUNT_SCREW_POSITIONS_MM
    )
)
BOARD_PRINTED_PART_SIZES_MM = (BOARD_TRAY_OUTER_SIZE_MM,)
BOARD_LONGEST_PRINTED_PART_MM = max(BOARD_TRAY_OUTER_SIZE_MM)
BOARD_PRINTED_PART_ENVELOPE_MM = BOARD_TRAY_OUTER_SIZE_MM
BOARD_ASSEMBLED_ENVELOPE_MM = BOARD_TRAY_OUTER_SIZE_MM


def usable_build_volume(
    build_volume_mm: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Return the build volume after reserving an edge margin on every side."""
    return tuple(
        axis - 2.0 * PRINT_BED_EDGE_MARGIN_MM for axis in build_volume_mm
    )


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
    if not (
        COMPACT_BOARD_MIN_SPAN_MM
        <= BOARD_FINISHED_SPAN_MM
        <= COMPACT_BOARD_MAX_SPAN_MM
    ):
        raise ValueError("Finished board span is outside the compact product range")
    if BOARD_HEIGHT_MM > COMPACT_BOARD_MAX_HEIGHT_MM:
        raise ValueError("Finished board is too tall for the compact product range")
    if not COMPACT_TILE_MIN_HEIGHT_MM <= TILE_HEIGHT_MM <= COMPACT_TILE_MAX_HEIGHT_MM:
        raise ValueError("Assembled tile height is outside the compact product range")
    if not isclose(PLAYING_SPAN_MM, SQUARE_SIZE_MM * GRID_COUNT):
        raise ValueError("Playing span must equal square size multiplied by grid count")
    if not isclose(
        BOARD_FINISHED_SPAN_MM,
        PLAYING_SPAN_MM + 2.0 * BOARD_FRAME_WIDTH_MM,
    ):
        raise ValueError("Finished span must include the printed frame on both sides")
    if not isclose(
        TILE_HEIGHT_MM,
        TILE_BOTTOM_HEIGHT_MM + TILE_TOP_THICKNESS_MM,
    ):
        raise ValueError("Tile top and bottom heights must add up to tile height")
    if not isclose(
        BOARD_HEIGHT_MM,
        BOARD_FLOOR_THICKNESS_MM + TILE_HEIGHT_MM,
    ):
        raise ValueError("Board floor and tile height must add up to tray height")
    if TILE_SIZE_MM <= 0.0 or TILE_SIZE_MM > SQUARE_SIZE_MM:
        raise ValueError("Tile size must fit within its square pitch")

    fit_clearances = {
        "tile edge per side": TILE_EDGE_CLEARANCE_PER_SIDE_MM,
        "lid": TILE_LID_CLEARANCE_MM,
    }
    for name, clearance in fit_clearances.items():
        if not FDM_MIN_FIT_CLEARANCE_MM <= clearance <= FDM_MAX_FIT_CLEARANCE_MM:
            raise ValueError(f"{name} clearance is outside the prototype fit range")

    minimum_features = {
        "bottom floor": TILE_BOTTOM_FLOOR_MM,
        "bottom wall": TILE_BOTTOM_WALL_MM,
        "lid rebate edge": TILE_LID_REBATE_EDGE_MM,
        "lid rail": TILE_LID_RAIL_WIDTH_MM,
        "magnet ring": TILE_MAGNET_RING_WIDTH_MM,
        "magnet top skin": TILE_MAGNET_TOP_SKIN_MM,
        "LED top skin": TILE_LED_TOP_SKIN_MM,
        "screw boss": TILE_MOUNT_SCREW_BOSS_DIAMETER_MM,
        "screw clearance hole": TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM,
        "board floor": BOARD_FLOOR_THICKNESS_MM,
        "board frame": BOARD_FRAME_WIDTH_MM,
    }
    for name, dimension in minimum_features.items():
        minimum = FDM_MIN_FLOOR_MM if name == "bottom floor" else FDM_MIN_FEATURE_MM
        if dimension < minimum:
            raise ValueError(f"{name} is below the prototype printable minimum")

    if TILE_INTERNAL_CAVITY_SIZE_MM <= 0.0:
        raise ValueError("Tile walls leave no internal cavity")
    if TILE_VELCRO_PAD_DEPTH_MM >= TILE_BOTTOM_FLOOR_MM - FDM_MIN_FLOOR_MM:
        raise ValueError("Velcro pockets must leave a printable tray floor")
    if TILE_MOUNT_SCREW_HEAD_DIAMETER_MM >= TILE_MOUNT_SCREW_BOSS_DIAMETER_MM:
        raise ValueError("Screw boss must surround the recessed screw head")
    if TILE_MOUNT_SCREW_HEAD_DEPTH_MM >= TILE_MOUNT_SCREW_BOSS_HEIGHT_MM:
        raise ValueError("Screw head recess must leave a bearing shoulder")
    if BOARD_MOUNT_SCREW_PILOT_DEPTH_MM >= BOARD_FLOOR_THICKNESS_MM:
        raise ValueError("Board screw pilots must remain blind")
    if BOARD_MOUNT_SCREW_PILOT_DIAMETER_MM >= TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM:
        raise ValueError("Board pilot holes must be smaller than tile clearance holes")
    expected_pilot_count = (
        GRID_COUNT * GRID_COUNT * len(TILE_MOUNT_SCREW_POSITIONS_MM)
    )
    if len(BOARD_MOUNT_SCREW_PILOT_POSITIONS_MM) != expected_pilot_count:
        raise ValueError("Board must contain one pilot for every tile screw hole")
    pilot_xy = {
        (x, y) for _, _, _, x, y in BOARD_MOUNT_SCREW_PILOT_POSITIONS_MM
    }
    if len(pilot_xy) != expected_pilot_count:
        raise ValueError("Board screw pilot positions must be unique")
    if TILE_LID_RAIL_INNER_SPAN_MM <= 0.0:
        raise ValueError("Tile lid rails leave no internal opening")
    if MAGNET_RING_INNER_DIAMETER_MM >= MAGNET_RING_OUTER_DIAMETER_MM:
        raise ValueError("Magnet ring inner diameter must be smaller than outer diameter")
    if MAGNET_RING_OUTER_DIAMETER_MM >= TILE_SIZE_MM:
        raise ValueError("Magnet ring must fit within the tile")
    if MAGNET_RING_DEPTH_MM >= TILE_TOP_THICKNESS_MM:
        raise ValueError("Magnet recess must leave a closed top skin")
    if any(aperture > pocket for aperture, pocket in zip(LED_APERTURE_MM, LED_POCKET_MM)):
        raise ValueError("LED aperture must not exceed the underside pocket")
    required_led_pocket_xy = tuple(
        package + 2.0 * LED_PACKAGE_CLEARANCE_PER_SIDE_MM
        for package in LED_PACKAGE_MAX_SIZE_MM[:2]
    )
    if any(
        pocket < required
        for pocket, required in zip(LED_POCKET_MM[:2], required_led_pocket_xy)
    ):
        raise ValueError("LED pocket does not clear the maximum 5050 package")
    if LED_POCKET_MM[2] < (
        LED_PACKAGE_MAX_SIZE_MM[2] + LED_PACKAGE_VERTICAL_CLEARANCE_MM
    ):
        raise ValueError("LED pocket is too shallow for the maximum 5050 package")
    if any(
        aperture < emitter + LED_PACKAGE_TOLERANCE_MM
        for aperture, emitter in zip(LED_APERTURE_MM, LED_EMITTER_WINDOW_MM)
    ):
        raise ValueError("LED aperture does not clear the emitter window")
    if any(
        aperture >= package
        for aperture, package in zip(
            LED_APERTURE_MM, LED_PACKAGE_NOMINAL_SIZE_MM[:2]
        )
    ):
        raise ValueError("LED aperture must retain the package body below the lid")

    tile_half = TILE_SIZE_MM / 2.0
    for axis, position in enumerate(LED_POSITION_MM):
        pocket_margin = tile_half - abs(position) - LED_POCKET_MM[axis] / 2.0
        if pocket_margin < TILE_BOTTOM_WALL_MM:
            raise ValueError("LED pocket leaves insufficient material at the tile edge")
        pcb_margin = tile_half - TILE_BOTTOM_WALL_MM - abs(position) - (
            LED_BREAKOUT_PCB_MM[axis] / 2.0
        )
        if pcb_margin < 0.0:
            raise ValueError("LED breakout PCB does not fit inside the tray cavity")

    nearest_pocket_radius = (
        (LED_POSITION_MM[0] - LED_POCKET_MM[0] / 2.0) ** 2
        + (LED_POSITION_MM[1] - LED_POCKET_MM[1] / 2.0) ** 2
    ) ** 0.5
    magnet_clearance = nearest_pocket_radius - MAGNET_RING_OUTER_DIAMETER_MM / 2.0
    if magnet_clearance < FDM_MIN_FEATURE_MM:
        raise ValueError("LED pocket collides with the hidden magnet recess")

    lid_rail_offset = (
        TILE_LID_RAIL_OUTER_SPAN_MM - TILE_LID_RAIL_WIDTH_MM
    ) / 2.0
    lid_rail_inner_edge = lid_rail_offset - TILE_LID_RAIL_WIDTH_MM / 2.0
    for axis, position in enumerate(LED_POSITION_MM):
        pocket_edge = abs(position) + LED_POCKET_MM[axis] / 2.0
        if lid_rail_inner_edge - pocket_edge < FDM_MIN_FEATURE_MM:
            raise ValueError("LED pocket collides with a lid locating rail")

    cavity_half = TILE_INTERNAL_CAVITY_SIZE_MM / 2.0
    if REED_SENSOR_BODY_MM[0] / 2.0 > cavity_half:
        raise ValueError("Reed sensor body does not fit inside the tray")
    if TILE_WIRE_PORT_WIDTH_MM < 3.0 * ELECTRONICS_WIRE_DIAMETER_MM:
        raise ValueError("Wire port cannot carry the three-wire LED bus")

    if len(BOARD_LED_POSITIONS_MM) != GRID_COUNT * GRID_COUNT:
        raise ValueError("Board composition must contain one LED per tile")
    if len({(x, y) for _, _, x, y in BOARD_LED_POSITIONS_MM}) != GRID_COUNT * GRID_COUNT:
        raise ValueError("Every composed LED position must be unique")

    wire_port_bottom = TILE_WIRE_PORT_CENTER_Z_MM - TILE_WIRE_PORT_HEIGHT_MM / 2.0
    wire_port_top = TILE_WIRE_PORT_CENTER_Z_MM + TILE_WIRE_PORT_HEIGHT_MM / 2.0
    if wire_port_bottom < TILE_BOTTOM_FLOOR_MM or wire_port_top > TILE_BOTTOM_HEIGHT_MM:
        raise ValueError("Wire port must remain between the tray floor and rim")

    if not fits_build_volume(
        TILE_PRINTED_PART_ENVELOPE_MM,
        REFERENCE_COMPACT_BUILD_VOLUME_MM,
    ):
        raise ValueError("Tile parts exceed the compact reference printer")
    for part_size in BOARD_PRINTED_PART_SIZES_MM:
        if not fits_build_volume(part_size, REFERENCE_LARGE_BUILD_VOLUME_MM):
            raise ValueError("Printable board exceeds the large-format reference printer")


validate()


if __name__ == "__main__":
    print(
        "CAD dimensions valid: "
        f"{GRID_COUNT} x {SQUARE_SIZE_MM:g} mm = {PLAYING_SPAN_MM:g} mm "
        f"playing span; {BOARD_FINISHED_SPAN_MM:g} mm "
        f"({BOARD_FINISHED_SPAN_MM / MILLIMETRES_PER_INCH:.1f} in) finished; "
        f"{BOARD_LONGEST_PRINTED_PART_MM:g} mm printable board"
    )
