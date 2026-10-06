"""Playing grid, populated-board geometry, and sensor-bank positions.

Role: the root of the dimension chain: the 8 x 8 grid, the LED and Hall sensor
positions in each square, the expander positions per Hall bank, and the PCB envelope.
`tile_plate.py`, `case.py` and `panel.py` build on these values. Product body sizes come
from `shared.components` so the PCB and CAD see the same package. Coordinates are board
millimetres, origin at the playing-area centre, Y up.
"""

from math import ceil
from types import MappingProxyType

from shared.components import HALL_SENSOR, SK9822, TCA9554
from shared.hall_banks import banks
from shared.squares import SquareLayout

# Project form factor. This is a compact electronic board, not a FIDE-sized board.
# These limits are guard rails for `validate()`, not manufacturing data: changing the
# format means reviewing every size derived below.
BOARD_FORMAT = "compact electronic"
COMPACT_SQUARE_MIN_MM = 35.0
COMPACT_SQUARE_MAX_MM = 45.0
COMPACT_BOARD_MIN_SPAN_MM = 300.0
COMPACT_BOARD_MAX_SPAN_MM = 400.0
COMPACT_BOARD_MAX_HEIGHT_MM = 35.0
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
LED_PACKAGE_CLEARANCE_PER_SIDE_MM = 0.2
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
# Interface with the PCB: nothing on the bottom side within this distance of the
# board edge, because the case ledge that carries the board reaches under it.
PCB_BOTTOM_EDGE_KEEPOUT_MM = 3.0

# --- Derived per-square layout ----------------------------------------------
# The one shared layout (centres, LED/Hall positions, chain order). PCB assemblies and
# CAD both read it, and it validates itself on construction.

BOARD_SQUARES = SquareLayout.build(
    grid_count=GRID_COUNT,
    square_size=SQUARE_SIZE_MM,
    playing_span=PLAYING_SPAN_MM,
    led_offset_mm=LED_POSITION_MM,
    hall_offset_mm=HALL_SENSOR_POSITION_MM,
)
