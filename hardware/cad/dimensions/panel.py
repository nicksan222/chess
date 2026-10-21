"""Control-strip openings and display fit in the tile plate.

Role: the button and OLED module fit numbers the plate bezel is cut from. Button
positions, the strip origin and the module drawing come from the PCB export
(`board.py`); the plate's own clearances, ledges and fasteners are defined here.
"""

from .board import (
    DISPLAY,
    PANEL_ORIGIN_Y_MM,
    PANEL_STRIP_DEPTH_MM,
    PLAYING_SPAN_MM,
)
from .case import PCB_TOP_Z_MM

# --- Control panel ----------------------------------------------------------
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
PANEL_OLED_MODULE_MM = DISPLAY.body_mm
PANEL_OLED_SCREEN_SIZE_MM = DISPLAY.screen_mm
PANEL_OLED_SCREEN_OFFSET_MM = DISPLAY.screen_offset_mm
PANEL_OLED_MOUNT_HOLES_MM = DISPLAY.mount_holes_mm
PANEL_OLED_MOUNT_HOLE_DIAMETER_MM = DISPLAY.mount_hole_diameter_mm
PANEL_OLED_UNDERSIDE_SIZE_MM = DISPLAY.underside_mm
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
PANEL_OLED_PCB_THICKNESS_MM = DISPLAY.pcb_thickness_mm
PANEL_OLED_UNDERSIDE_HEIGHT_MM = PANEL_OLED_UNDERSIDE_SIZE_MM[2]
PANEL_OLED_FRAME_MM = DISPLAY.frame_mm
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
# TL1105 housing height, E-Switch catalog pp.24-25. The plate is relieved above
# each housing so print and board tolerances cannot land the plate on it.
PANEL_BUTTON_RELIEF_DEPTH_MM = 1.0
PANEL_BUTTON_RELIEF_CLEARANCE_MM = 0.5
# TL1105 "C" round stem, E-Switch catalog pp.24-25.
# The stem must stand proud of the bezel to be pressed, but not so far that it
# snags or levers on the switch.
PANEL_BUTTON_MIN_PROTRUSION_MM = 0.5
PANEL_BUTTON_MAX_PROTRUSION_MM = 2.0
