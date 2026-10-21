"""Board geometry the PCB owns: grid, squares, sensor banks, outline, holes, placements.

Role: the root of the board dimension chain: the 8 x 8 grid, the LED and Hall sensor
positions in each square, the expander positions per Hall bank, the PCB envelope, its
mounting holes and `PCB_STRIP_PLACEMENTS`, the single table of hand-placed parts.
Product body sizes come from `pcb.spec.components`. Coordinates are board millimetres,
origin at the playing-area centre, Y up. The PCB places parts from these values and
exports them in `generated/pcb-components.json`, which the case and plate are built
from.
"""

from dataclasses import dataclass
from math import ceil, isclose
from types import MappingProxyType

from pcb.spec.components import HALL_SENSOR, SK9822, TCA9554
from pcb.spec.components.button import BUTTON_HOUSING_MM
from pcb.spec.hall_banks import banks
from pcb.spec.panel_buttons import PANEL_BUTTONS
from pcb.spec.squares import SquareLayout

# Project form factor. This is a compact electronic board, not a FIDE-sized board.
# These limits are guard rails for `validate()`, not manufacturing data: changing the
# format means reviewing every size derived below.
BOARD_FORMAT = "compact electronic"
COMPACT_SQUARE_MIN_MM = 35.0
COMPACT_SQUARE_MAX_MM = 45.0
COMPACT_BOARD_MIN_SPAN_MM = 300.0
COMPACT_BOARD_MAX_SPAN_MM = 400.0
FIDE_REFERENCE_SQUARE_MIN_MM = 50.0
FIDE_REFERENCE_SQUARE_MAX_MM = 60.0

# Board grid. Unchanged from revision A: 40 mm squares suit a chess set with a
# king base of 32 mm or less, which covers most ordinary club sets.
GRID_COUNT = 8
SQUARE_SIZE_MM = 40.0
PLAYING_SPAN_MM = SQUARE_SIZE_MM * GRID_COUNT

# Opsco SK9822-A 5050 addressable RGB LED (SPC/SK9822-A Rev 01): body
# 5.4 x 5.0 x 1.6 mm, "tolerance is ±0.1 mm unless otherwise noted" (p3).
LED_PACKAGE_REFERENCE = SK9822.description
LED_PACKAGE_NOMINAL_SIZE_MM = SK9822.require_body_mm()
LED_PACKAGE_TOLERANCE_MM = 0.1
LED_PACKAGE_MAX_SIZE_MM = tuple(
    axis + LED_PACKAGE_TOLERANCE_MM for axis in LED_PACKAGE_NOMINAL_SIZE_MM
)
LED_EMITTER_WINDOW_MM = (4.0, 4.0)
# LED offset from the square centre, where the Hall sensor sits (HALL_SENSOR_POSITION_MM).
LED_POSITION_MM = (13.0, 13.0)

# SOT-23 omnipolar Hall sensor at each square centre. Either magnet pole drives
# its active-low output, preserving the old occupied-square electrical polarity.
HALL_SENSOR_PACKAGE_MM = HALL_SENSOR.require_body_mm()
HALL_SENSOR_BODY_MM = HALL_SENSOR_PACKAGE_MM[:2]
HALL_SENSOR_HEIGHT_MM = HALL_SENSOR_PACKAGE_MM[2]
HALL_SENSOR_POSITION_MM = (0.0, 0.0)
HALL_SENSOR_STANDOFF_MM = 0.0
# Expander package orientation and centres are exported because the case must clear
# the same physical obstructions that PCB placement and routing use.
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
# One board spans the playing area plus a 60 mm control strip along the front,
# so the buttons and display face up and solder flat like everything else.
PCB_THICKNESS_MM = 1.6
PANEL_STRIP_DEPTH_MM = 60.0
PCB_SIZE_MM = (
    PLAYING_SPAN_MM,
    PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM,
    PCB_THICKNESS_MM,
)
PCB_CENTER_OFFSET_Y_MM = -PANEL_STRIP_DEPTH_MM / 2.0
# Interface with the PCB: nothing on the bottom side within this distance of the
# board edge, because the case ledge that carries the board reaches under it.
PCB_BOTTOM_EDGE_KEEPOUT_MM = 3.0

# --- Mounting holes ---------------------------------------------------------
# A 320 mm board flexes badly on perimeter support alone, so the case bosses stand
# under holes on the grid lines, where no LED or Hall sensor sits, plus four along
# the control strip. The case stands one boss under each exported hole.
PCB_MOUNTING_HOLE_DIAMETER_MM = 3.4
PCB_MOUNTING_GRID_OFFSETS_MM = (-120.0, -40.0, 40.0, 120.0)
PCB_MOUNTING_HOLE_POSITIONS_MM = tuple(
    (x, y) for y in PCB_MOUNTING_GRID_OFFSETS_MM for x in PCB_MOUNTING_GRID_OFFSETS_MM
) + tuple(
    (x, -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0)
    for x in (-144.0, -48.0, 48.0, 144.0)
)

# --- Control strip ----------------------------------------------------------
PANEL_ORIGIN_Y_MM = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0

# --- Derived per-square layout ----------------------------------------------
# The one square layout (centres, LED/Hall positions, chain order). PCB assemblies read
# it, the export publishes it, and it validates itself on construction.

BOARD_SQUARES = SquareLayout.build(
    grid_count=GRID_COUNT,
    square_size=SQUARE_SIZE_MM,
    playing_span=PLAYING_SPAN_MM,
    led_offset_mm=LED_POSITION_MM,
    hall_offset_mm=HALL_SENSOR_POSITION_MM,
)


Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoardPlacement:
    """Centre, rotation and side of a hand-placed footprint.

    `bottom=True` places a through-hole part on the PCB underside; the PCB code flips it.
    """

    centre_mm: Point
    rotation_degrees: float = 0.0
    bottom: bool = False

    @property
    def x_mm(self) -> float:
        return self.centre_mm[0]

    @property
    def y_mm(self) -> float:
        return self.centre_mm[1]


# Reference designator -> placement (board mm, Y up; centre-origin of the footprint). Parts
# not listed here are placed by their own assembly (squares, Hall banks, buttons). The
# comments record why a part sits where it does: most positions are fixed by the PCB
# tests (decoupling distance, selective-solder spacing, silkscreen/mask webs).
PCB_STRIP_PLACEMENTS = MappingProxyType(
    {
        # Power entry (S3a, interface H1/H2): J4 hole row at (-105, +128) on the
        # bottom, opening +Y toward the rear-wall jack and rocker; footprint origin
        # is the body centre, 4.45 mm past the hole row toward the opening.
        "J4": BoardPlacement((-105.0, 132.45), 180.0, bottom=True),
        # Seen from below, J4 circuit 1 is on the right (JST VH p4 is drawn from
        # the mounting side), so DC_IN is at -X and +5V at +X from the top (S3c B1).
        "F1": BoardPlacement((-108.0, 121.0)),
        # S4b eFuse cluster (top side): U74 between the DC_FUSED loop (west, fed
        # from J4.3) and its +5V via rows (east); bias parts in the open area east.
        "U74": BoardPlacement((-92.0, 132.5)),
        # S4c (manufacturing review): >= 5 mm from J4's top-side joints so J4 can
        # be selectively soldered.
        "D1": BoardPlacement((-106.5, 135.4), 180.0),
        "C141": BoardPlacement((-94.4, 136.9), 90.0),
        # S4c/S6: 3 mm from J4-4 to R4's courtyard, for selective soldering.
        "R4": BoardPlacement((-97.4, 133.0), 180.0),
        "C142": BoardPlacement((-89.3, 130.1)),
        "R3": BoardPlacement((-88.9, 132.5), 270.0),
        "C143": BoardPlacement((-88.4, 135.0)),
        # S4c: OVLO spike filter in R5's row, pin 1 facing R5's OVLO pad.
        "C144": BoardPlacement((-85.9, 130.6), 180.0),
        "R5": BoardPlacement((-83.0, 130.6)),
        "R6": BoardPlacement((-83.0, 133.2)),
        "R7": BoardPlacement((-75.5, 133.2)),
        "R8": BoardPlacement((-83.0, 135.8)),
        "C2": BoardPlacement((-87.6, 139.0)),
        "C1": BoardPlacement((-66.0, 132.0), bottom=True),
        "C140": BoardPlacement((-56.0, 132.0), bottom=True),
        # OLED harness header, opening -Y toward the plate-mounted module's pads.
        # Interface M6: the mated SHR housing and wire bend end before the module
        # zone (y <= -166.5).
        "J2": BoardPlacement((-110.0, -158.5)),
        "U5": BoardPlacement((-70.0, -180.0)),
        "C7": BoardPlacement((-66.5, -174.2)),
        # S5: R9 terminates LED data beside U5; TP3/TP4 sit inline on the data and
        # clock runs (no long probe stubs on the first LED links).
        "R9": BoardPlacement((-79.0, -178.73)),
        # S6 LED rail switch (interface H5), between U5 and the H18 boss: Q1
        # (SO-8) with its source and drain via rows, Q2 and the gate drive.
        "Q1": BoardPlacement((-55.0, -188.0)),
        "C145": BoardPlacement((-55.0, -192.8)),
        "R16": BoardPlacement((-60.0, -192.8)),
        "Q2": BoardPlacement((-55.0, -179.5)),
        "R13": BoardPlacement((-50.0, -183.0), 180.0),
        "R14": BoardPlacement((-50.0, -179.0)),
        "R15": BoardPlacement((-59.5, -176.0)),
        # S6b (H6): U75 Schmitt OR below U5, its output facing U5's enable pins;
        # C146 just south of its supply and ground pins.
        "U75": BoardPlacement((-70.0, -190.0), 180.0),
        "C146": BoardPlacement((-70.0, -193.0)),
        "TP1": BoardPlacement((-47.0, -165.0)),
        "TP2": BoardPlacement((-40.0, -165.0)),
        "TP3": BoardPlacement((-87.5, -178.73)),
        "TP4": BoardPlacement((-83.0, -182.5)),
        # S6d: R17/R18 pull LED_DATA_5V/LED_CLK_5V down beside their test points.
        "R17": BoardPlacement((-87.5, -182.5)),
        "R18": BoardPlacement((-83.0, -185.5)),
        "TP5": BoardPlacement((-19.0, -165.0)),
        "TP6": BoardPlacement((-12.0, -165.0)),
        "TP7": BoardPlacement((-47.0, -196.0)),
    }
)


def _inside_board(point: Point, margin: float = 0.0) -> bool:
    """True if a board-frame point lies inside the PCB outline less `margin`."""
    half_x = PCB_SIZE_MM[0] / 2.0 - margin
    half_y = PCB_SIZE_MM[1] / 2.0 - margin
    return abs(point[0]) <= half_x and abs(point[1] - PCB_CENTER_OFFSET_Y_MM) <= half_y


def validate() -> None:
    """Reject board geometry that is inconsistent or cannot be placed."""
    if GRID_COUNT != 8:
        raise ValueError("A chessboard must contain eight rows and eight columns")
    if BOARD_FORMAT != "compact electronic":
        raise ValueError("Review all scale guardrails when changing the board format")
    if not COMPACT_SQUARE_MIN_MM <= SQUARE_SIZE_MM <= COMPACT_SQUARE_MAX_MM:
        raise ValueError("Square size is outside the compact-board design range")
    if not isclose(PLAYING_SPAN_MM, SQUARE_SIZE_MM * GRID_COUNT):
        raise ValueError("Playing span must equal square size multiplied by grid count")
    for span in PCB_SIZE_MM[:2]:
        if not COMPACT_BOARD_MIN_SPAN_MM <= span <= COMPACT_BOARD_MAX_SPAN_MM:
            raise ValueError("Board outline is outside the compact product range")
    if not isclose(PCB_SIZE_MM[0], PLAYING_SPAN_MM):
        raise ValueError("Board must be exactly as wide as the playing area")
    if not isclose(PCB_SIZE_MM[1], PLAYING_SPAN_MM + PANEL_STRIP_DEPTH_MM):
        raise ValueError("Board must carry the playing area and the control strip")
    if max(HALL_SENSOR_BODY_MM) >= SQUARE_SIZE_MM:
        raise ValueError("Hall sensor body does not fit within one square")
    if len(EXPANDER_POSITIONS_BY_BANK_MM) != 8:
        raise ValueError("Board composition must place eight GPIO expanders")
    if len(set(EXPANDER_POSITIONS_BY_BANK_MM.values())) != 8:
        raise ValueError("GPIO expander positions must be unique")
    BOARD_SQUARES.validate_topology()

    # Mounting holes stand on the grid lines; no LED or Hall sensor may be there.
    # The case checks its own, wider boss against the exported positions.
    keepout = PCB_MOUNTING_HOLE_DIAMETER_MM / 2.0
    if len(set(PCB_MOUNTING_HOLE_POSITIONS_MM)) != len(PCB_MOUNTING_HOLE_POSITIONS_MM):
        raise ValueError("Mounting hole positions must be unique")
    for hole in PCB_MOUNTING_HOLE_POSITIONS_MM:
        if not _inside_board(hole, keepout + PCB_BOTTOM_EDGE_KEEPOUT_MM):
            raise ValueError("A mounting hole reaches the board-edge keep-out")
        for square in BOARD_SQUARES:
            for feature, size in (
                (square.led_position_mm, LED_PACKAGE_MAX_SIZE_MM),
                (square.hall_position_mm, HALL_SENSOR_BODY_MM),
            ):
                if (
                    abs(hole[0] - feature[0]) < keepout + size[0] / 2.0
                    and abs(hole[1] - feature[1]) < keepout + size[1] / 2.0
                ):
                    raise ValueError("A mounting hole collides with a square feature")

    # Control buttons stay on the control strip.
    strip_min_y = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM
    strip_max_y = -PLAYING_SPAN_MM / 2.0
    half_housing = max(BUTTON_HOUSING_MM[:2]) / 2.0
    for button in PANEL_BUTTONS:
        x, y = button.position_mm
        if not (strip_min_y <= y - half_housing and y + half_housing <= strip_max_y):
            raise ValueError(f"Button {button.name} extends off the control strip")
        if abs(x) + half_housing > PLAYING_SPAN_MM / 2.0:
            raise ValueError(f"Button {button.name} extends off the board")
    if len(PANEL_BUTTONS) != 12:
        raise ValueError("Control panel must place every button")
    if len({button.position_mm for button in PANEL_BUTTONS}) != len(PANEL_BUTTONS):
        raise ValueError("Button positions must be unique")
    for reference, placement in PCB_STRIP_PLACEMENTS.items():
        if not _inside_board(placement.centre_mm):
            raise ValueError(f"{reference} is placed outside the board")


# Fail on import, so every consumer inherits the guarantee.
validate()
