"""Control-strip openings, display fit, and shared PCB placements."""

from dataclasses import dataclass
from types import MappingProxyType

from shared.components import BUTTON, OLED_MODULE

from .board import PANEL_STRIP_DEPTH_MM, PLAYING_SPAN_MM

# --- Control panel ----------------------------------------------------------
PANEL_ORIGIN_Y_MM = -PLAYING_SPAN_MM / 2.0 - PANEL_STRIP_DEPTH_MM / 2.0
PANEL_BUTTON_COUNT = 12
PANEL_BUTTON_HOLE_DIAMETER_MM = 7.0

# AZ-Delivery 0.96 in SSD1306 module. The window exposes its approximately
# 23.7 x 12.9 mm viewing area; the recess holds the 27 x 27 mm carrier board,
# connected to J2 by four short wires.
PANEL_OLED_MODULE_MM = OLED_MODULE.require_body_mm()
PANEL_OLED_WINDOW_MM = (23.7, 12.9)
# Per-side XY clearance for printed-part tolerance and hand assembly.
PANEL_OLED_RECESS_CLEARANCE_XY_MM = 0.5
PANEL_OLED_RECESS_MM = tuple(
    dimension + 2.0 * PANEL_OLED_RECESS_CLEARANCE_XY_MM
    for dimension in PANEL_OLED_MODULE_MM[:2]
)
PANEL_OLED_RECESS_DEPTH_MM = 2.0
PANEL_OLED_CENTER_MM = (-110.0, PANEL_ORIGIN_Y_MM)
PANEL_BUTTON_BODY_MM = (*BUTTON.require_body_mm()[:2], 5.0)
PANEL_BUTTON_ACTUATOR_DIAMETER_MM = 3.5
Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoardPlacement:
    centre_mm: Point
    rotation_degrees: float = 0.0

    @property
    def x_mm(self) -> float:
        return self.centre_mm[0]

    @property
    def y_mm(self) -> float:
        return self.centre_mm[1]


PCB_STRIP_PLACEMENTS = MappingProxyType(
    {
        "J3": BoardPlacement((-150.0, -178.0), -90.0),
        "F1": BoardPlacement((-138.0, -178.0)),
        "D1": BoardPlacement((-150.0, -165.0)),
        "SW13": BoardPlacement((-113.0, -190.0)),
        "C1": BoardPlacement((-128.0, -170.0)),
        "C2": BoardPlacement((-116.0, -168.0)),
        "J2": BoardPlacement((-95.0, -172.0)),
        "U5": BoardPlacement((-70.0, -180.0)),
        "C7": BoardPlacement((-58.0, -180.0)),
        "R1": BoardPlacement((-50.0, -170.0)),
        "R2": BoardPlacement((-50.0, -176.0)),
        "TP1": BoardPlacement((-47.0, -165.0)),
        "TP2": BoardPlacement((-40.0, -165.0)),
        "TP3": BoardPlacement((-33.0, -165.0)),
        "TP4": BoardPlacement((-26.0, -165.0)),
        "TP5": BoardPlacement((-19.0, -165.0)),
        "TP6": BoardPlacement((-12.0, -165.0)),
        "TP7": BoardPlacement((-47.0, -196.0)),
    }
)
