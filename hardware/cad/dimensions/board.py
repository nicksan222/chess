"""The board the enclosure is built around, read from the PCB's published export.

Role: the only door from the PCB into the case and plate. The PCB build writes
`hardware/pcb/generated/pcb-components.json`; this module reads it once and exposes
its board facts under the names the enclosure code uses. Nothing here is authored:
to move a square, a hole, a button or the Pi, change the PCB and regenerate it.
Coordinates are board millimetres, origin at the playing-area centre, Y up.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from cad.harness.base.pcb import PcbPart, PcbSnapshot

PCB_EXPORT_PATH = (
    Path(__file__).resolve().parents[2] / "pcb" / "generated" / "pcb-components.json"
)
PCB = PcbSnapshot.read(PCB_EXPORT_PATH)
BOARD = PCB.interface
PCB_PARTS = MappingProxyType({part.reference: part for part in PCB.parts})

# Grid and outline.
GRID_COUNT = BOARD.grid_count
SQUARE_SIZE_MM = BOARD.square_size_mm
PLAYING_SPAN_MM = BOARD.playing_span_mm
PANEL_STRIP_DEPTH_MM = BOARD.panel_strip_depth_mm
PANEL_ORIGIN_Y_MM = BOARD.panel_origin_y_mm
PCB_SIZE_MM = BOARD.pcb_size_mm
PCB_THICKNESS_MM = PCB_SIZE_MM[2]
PCB_CENTER_OFFSET_Y_MM = BOARD.pcb_center_offset_y_mm
# Nothing on the PCB underside within this distance of the edge: the case ledge.
PCB_BOTTOM_EDGE_KEEPOUT_MM = BOARD.bottom_edge_keepout_mm
BOARD_SQUARES = BOARD.squares

# Square features the plate pockets and ribs must clear.
LED_POSITION_MM = BOARD.led_offset_mm
LED_PACKAGE_MAX_SIZE_MM = BOARD.led_package_max_mm
LED_PACKAGE_TOLERANCE_MM = BOARD.led_package_tolerance_mm
LED_EMITTER_WINDOW_MM = BOARD.led_emitter_window_mm
HALL_SENSOR_BODY_MM = BOARD.hall_sensor_mm[:2]
HALL_SENSOR_HEIGHT_MM = BOARD.hall_sensor_mm[2]
HALL_SENSOR_STANDOFF_MM = BOARD.hall_sensor_standoff_mm
EXPANDER_BODY_MM = BOARD.expander_mm
EXPANDER_POSITIONS_BY_BANK_MM = MappingProxyType(BOARD.expanders_mm)

# One case boss stands under each PCB mounting hole.
PCB_MOUNTING_HOLE_DIAMETER_MM = BOARD.mounting_hole_diameter_mm
PCB_SUPPORT_POSITIONS_MM = BOARD.mounting_holes_mm

# The Pi hangs component side up from J1; the PCB owns where.
PI_BOARD_SIZE_MM = BOARD.host.board_mm
PI_CENTER_MM = BOARD.host.centre_mm
PI_ROTATION_DEG = BOARD.host.rotation_degrees
PI_BOARD_TO_BOARD_MM = BOARD.host.board_to_board_mm
PI_HEADER_HEIGHT_MM = BOARD.host.header_height_mm
PI_SD_SOCKET_MM = BOARD.host.sd_socket_mm
PI_SD_SOCKET_HEIGHT_MM = BOARD.host.sd_socket_height_mm

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class PanelButton:
    """One control button as the plate sees it: its label, switch and centre."""

    name: str
    switch_reference: str
    position_mm: Point

    @property
    def x_mm(self) -> float:
        return self.position_mm[0]

    @property
    def y_mm(self) -> float:
        return self.position_mm[1]

    @property
    def legend_position_mm(self) -> Point:
        """Recessed plate legend: above UP, below every other button."""
        return self.x_mm, self.y_mm + (8 if self.name == "UP" else -10)


@dataclass(frozen=True, slots=True)
class PanelButtons:
    """The exported buttons in PCB order, looked up by label."""

    buttons: tuple[PanelButton, ...]

    def __iter__(self) -> Iterator[PanelButton]:
        return iter(self.buttons)

    def __len__(self) -> int:
        return len(self.buttons)

    def by_name(self, name: str) -> PanelButton:
        """Look up a button by its label; raises KeyError if unknown."""
        for button in self.buttons:
            if button.name == name:
                return button
        raise KeyError(name)


def _button_part(reference: str) -> PcbPart:
    return PCB_PARTS[reference]


PANEL_BUTTONS = PanelButtons(
    tuple(
        PanelButton(name, reference, _button_part(reference).position_mm)
        for name, reference in PCB.buttons.items()
    )
)
_SWITCH = _button_part(PANEL_BUTTONS.buttons[0].switch_reference)
# The switch housing and its overall height above the PCB, stem included.
PANEL_BUTTON_BODY_MM = _SWITCH.housing_mm or _SWITCH.body_mm
PANEL_BUTTON_HEIGHT_MM = _SWITCH.body_mm[2]
PANEL_BUTTON_ACTUATOR_DIAMETER_MM = BOARD.button_actuator_diameter_mm

# Products wired to the board and mounted in the plate or the rear wall.
DISPLAY = BOARD.display
JACK = BOARD.jack
ROCKER = BOARD.rocker
HARNESS = BOARD.harness
