"""Control-strip openings, display fit, and shared PCB placements.

Role: where the controls sit on the 60 mm strip in front of the playing area, the
button and OLED module fit numbers the plate bezel is cut from, and
`PCB_STRIP_PLACEMENTS`, the single table of hand-placed parts on the board (power entry,
eFuse, LED switch, test points...). The PCB generator places parts from that table and
`hardware/cad` tests read it, so a part can move in one place only. Panel button
positions themselves come from `shared/panel_buttons.py`.
"""

from dataclasses import dataclass
from types import MappingProxyType

from shared.components import BUTTON, OLED_MODULE
from shared.components.button import BUTTON_ACTUATOR_DIAMETER_MM, BUTTON_HOUSING_MM
from shared.components.oled_module import (
    OLED_FRAME_MM,
    OLED_MOUNT_HOLE_DIAMETER_MM,
    OLED_MOUNT_HOLES_MM,
    OLED_PAD_POSITIONS_MM,
    OLED_PCB_THICKNESS_MM,
    OLED_SCREEN_OFFSET_MM,
    OLED_SCREEN_SIZE_MM,
    OLED_UNDERSIDE_SIZE_MM,
)

from .board import PANEL_STRIP_DEPTH_MM, PLAYING_SPAN_MM
from .case import PCB_TOP_Z_MM

# --- Control panel ----------------------------------------------------------
PANEL_ORIGIN_Y_MM = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0
PANEL_BUTTON_COUNT = 12
# The control strip sits below the playing surface. The full OLED module
# mounts in a raised bezel on four mounting ledges.
PANEL_SURFACE_RECESS_MM = 1.0
PANEL_SURFACE_MARGIN_MM = 4.0
PANEL_SURFACE_SIZE_MM = (
    PLAYING_SPAN_MM - 2 * PANEL_SURFACE_MARGIN_MM,
    PANEL_STRIP_DEPTH_MM - 2 * PANEL_SURFACE_MARGIN_MM,
)
# E-Switch TL1105 round stem through the bezel, now part of the tile plate.
PANEL_BUTTON_HOLE_DIAMETER_MM = 5.0

# MC242GW supplier drawing V1.0, header uninstalled (direct-solder harness).
PANEL_OLED_MODULE_MM = OLED_MODULE.require_body_mm()
PANEL_OLED_SCREEN_SIZE_MM = OLED_SCREEN_SIZE_MM
PANEL_OLED_SCREEN_OFFSET_MM = OLED_SCREEN_OFFSET_MM
PANEL_OLED_MOUNT_HOLES_MM = OLED_MOUNT_HOLES_MM
PANEL_OLED_MOUNT_HOLE_DIAMETER_MM = OLED_MOUNT_HOLE_DIAMETER_MM
PANEL_OLED_UNDERSIDE_SIZE_MM = OLED_UNDERSIDE_SIZE_MM
# Header pads from supplier drawing, pin 1 GND through pin 5 optional RES.
PANEL_OLED_PAD_POSITIONS_MM = OLED_PAD_POSITIONS_MM
PANEL_OLED_LEDGE_WIDTH_MM = 4.8
PANEL_OLED_LEDGE_BOTTOM_Z_MM = PCB_TOP_Z_MM + 0.5
PANEL_OLED_LEDGE_WALL_REACH_MM = 1.0
PANEL_OLED_PILOT_DIAMETER_MM = 2.0
# M2.5 x 3 DIN 912 / ISO 4762: head Ø4.5 x 2.5, 2 mm hex.
# https://www.newstarfastenings.com/en-gb/products/m25-x-3-socket-cap-screw-din-912-steel-129-self-finish
PANEL_OLED_SCREW_LENGTH_MM = 3.0
PANEL_OLED_SCREW_HEAD_DIAMETER_MM = 4.5
PANEL_OLED_SCREW_HEAD_HEIGHT_MM = 2.5
PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM = 5.0
PANEL_OLED_PCB_THICKNESS_MM = OLED_PCB_THICKNESS_MM
PANEL_OLED_UNDERSIDE_HEIGHT_MM = PANEL_OLED_UNDERSIDE_SIZE_MM[2]
PANEL_OLED_FRAME_MM = OLED_FRAME_MM
# Module PCB bottom is just above the owning plate's underside. Its SMD
# envelope clears the actual PCB beneath it, without cutting the PCB.
PANEL_OLED_PCB_BOTTOM_Z_MM = 26.5
PANEL_OLED_SCREEN_Z_MM = (
    PANEL_OLED_PCB_BOTTOM_Z_MM + PANEL_OLED_PCB_THICKNESS_MM + PANEL_OLED_FRAME_MM[2]
)
PANEL_OLED_BEZEL_ROOF_MM = 1.0
PANEL_OLED_BEZEL_TOP_Z_MM = PANEL_OLED_SCREEN_Z_MM + 0.1 + PANEL_OLED_BEZEL_ROOF_MM
PANEL_OLED_BEZEL_CLEARANCE_XY_MM = 0.5
PANEL_OLED_BEZEL_INNER_MM = tuple(
    dimension + 2 * PANEL_OLED_BEZEL_CLEARANCE_XY_MM
    for dimension in PANEL_OLED_MODULE_MM[:2]
)
PANEL_OLED_PILOT_FLOOR_MM = 1.0
PANEL_OLED_BEZEL_WALL_MM = 2.0
PANEL_OLED_BEZEL_OUTER_MM = tuple(
    side + 2 * PANEL_OLED_BEZEL_WALL_MM for side in PANEL_OLED_BEZEL_INNER_MM
)
PANEL_OLED_WIRE_OPENING_MM = (8.0, 4.0)
PANEL_OLED_CENTER_MM = (0.0, PANEL_ORIGIN_Y_MM)
PANEL_BUTTON_CAP_SIZE_MM = (10.0, 10.0, 2.8)
PANEL_BUTTON_CAP_BOTTOM_Z_MM = 29.4
PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM = 3.9
PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM = 31.15
PANEL_LEGEND_SIZE_MM = 3.8
PANEL_LEGEND_DEPTH_MM = 0.5
# Overall height of the approved TL1105 above the PCB, stem included.
PANEL_BUTTON_HEIGHT_MM = BUTTON.require_body_mm()[2]
# TL1105 housing height, E-Switch catalog pp.24-25. The plate is relieved above
# each housing so print and board tolerances cannot land the plate on it.
PANEL_BUTTON_BODY_MM = BUTTON_HOUSING_MM
PANEL_BUTTON_RELIEF_DEPTH_MM = 1.0
PANEL_BUTTON_RELIEF_CLEARANCE_MM = 0.5
# TL1105 "C" round stem, E-Switch catalog pp.24-25.
PANEL_BUTTON_ACTUATOR_DIAMETER_MM = BUTTON_ACTUATOR_DIAMETER_MM
# The stem must stand proud of the bezel to be pressed, but not so far that it
# snags or levers on the switch.
PANEL_BUTTON_MIN_PROTRUSION_MM = 0.5
PANEL_BUTTON_MAX_PROTRUSION_MM = 2.0
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
