"""Presentation-only stand-in for the populated circuit board.

None of this is printed and none of it is authoritative: the design contract under
`hardware/pcb` owns the design. These shapes exist so an assembly render
shows what fills the case, and so the vertical stack in `core/dimensions.py` can
be seen to add up rather than merely asserted.

Positions come from the shared dimensions, so if a square pitch or a board
thickness changes, the proxy moves with it.
"""

import bpy

from core import dimensions as shared
from core import materials, modeling

EXPANDER_BODY_MM = shared.EXPANDER_BODY_MM
EXPANDER_POSITIONS_MM = tuple(shared.EXPANDER_POSITIONS_BY_QUADRANT_MM.values())


def create_materials() -> dict[str, bpy.types.Material]:
    return {
        "pcb": materials.solid("Circuit board", (0.02, 0.16, 0.07, 1.0), 0.38),
        "body": materials.solid("Component body", (0.10, 0.10, 0.11, 1.0), 0.34),
        "emitter": materials.solid("RGB emitter window", (0.78, 0.86, 0.92, 1.0), 0.10),
        "host": materials.solid("Raspberry Pi board", (0.16, 0.05, 0.10, 1.0), 0.42),
        "display": materials.solid("OLED glass", (0.02, 0.02, 0.03, 1.0), 0.08),
    }


def add_board(collection: bpy.types.Collection) -> bpy.types.Object:
    """The board itself, plus everything standing on it."""
    palette = create_materials()

    board = modeling.rounded_box(
        "Proxy_Circuit_Board",
        shared.PCB_SIZE_MM,
        (
            0.0,
            shared.PCB_CENTER_OFFSET_Y_MM,
            shared.PCB_UNDERSIDE_Z_MM + shared.PCB_THICKNESS_MM / 2.0,
        ),
        0.6,
        collection,
    )
    board.data.materials.append(palette["pcb"])
    board["purpose"] = "Presentation proxy; the design contract owns the real design"

    _add_leds(collection, palette)
    _add_hall_sensors(collection, palette)
    _add_expanders(collection, palette)
    _add_host(collection, palette)
    _add_panel(collection, palette)
    return board


def _add_leds(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    height = shared.LED_PACKAGE_NOMINAL_SIZE_MM[2]
    for row, column, x, y in shared.BOARD_LED_POSITIONS_MM:
        led = modeling.rounded_box(
            f"Proxy_LED_{row:02d}_{column:02d}",
            shared.LED_PACKAGE_NOMINAL_SIZE_MM,
            (x, y, shared.PCB_TOP_Z_MM + height / 2.0),
            0.3,
            collection,
        )
        led.data.materials.append(palette["body"])
        led["reference"] = shared.LED_PACKAGE_REFERENCE
        emitter = modeling.rounded_box(
            f"Proxy_LED_Window_{row:02d}_{column:02d}",
            (*shared.LED_EMITTER_WINDOW_MM, 0.2),
            (x, y, shared.PCB_TOP_Z_MM + height),
            0.0,
            collection,
        )
        emitter.data.materials.append(palette["emitter"])


def _add_hall_sensors(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    height = shared.HALL_SENSOR_HEIGHT_MM
    for row, column, x, y in shared.BOARD_HALL_POSITIONS_MM:
        sensor = modeling.rounded_box(
            f"Proxy_Hall_{row:02d}_{column:02d}",
            (*shared.HALL_SENSOR_BODY_MM, height),
            (x, y, shared.PCB_TOP_Z_MM + height / 2.0),
            0.2,
            collection,
        )
        sensor.data.materials.append(palette["body"])


def _add_expanders(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    for index, (x, y) in enumerate(EXPANDER_POSITIONS_MM):
        chip = modeling.rounded_box(
            f"Proxy_Expander_{index}",
            EXPANDER_BODY_MM,
            (x, y, shared.PCB_TOP_Z_MM + EXPANDER_BODY_MM[2] / 2.0),
            0.4,
            collection,
        )
        chip.data.materials.append(palette["body"])
        chip["purpose"] = "SMD MCP23017, one per board quadrant"


def _add_host(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    """The Pi hangs under the board on its header, in the cavity."""
    top = shared.PCB_UNDERSIDE_Z_MM - shared.PI_HEADER_HEIGHT_MM
    pi_board = modeling.rounded_box(
        "Proxy_Raspberry_Pi",
        shared.PI_BOARD_SIZE_MM,
        (
            *shared.PI_BAY_CENTER_MM,
            top - shared.PI_BOARD_SIZE_MM[2] / 2.0,
        ),
        0.5,
        collection,
    )
    pi_board.data.materials.append(palette["host"])
    pi_board["purpose"] = "Raspberry Pi Zero 2 W; the only processor on the board"

    header = modeling.rounded_box(
        "Proxy_Pi_Header",
        shared.PI_HEADER_BODY_MM,
        (
            *shared.PI_BAY_CENTER_MM,
            top + shared.PI_HEADER_HEIGHT_MM / 2.0,
        ),
        0.4,
        collection,
    )
    header.data.materials.append(palette["body"])


def _add_panel(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    for index, (x, y) in enumerate(shared.PANEL_BUTTON_POSITIONS_MM):
        body = modeling.rounded_box(
            f"Proxy_Button_{index:02d}",
            shared.PANEL_BUTTON_BODY_MM,
            (
                x,
                y,
                shared.PCB_TOP_Z_MM + shared.PANEL_BUTTON_BODY_MM[2] / 2.0,
            ),
            0.4,
            collection,
        )
        body.data.materials.append(palette["body"])
        # The actuator has to reach the bezel, which is what sets its length.
        reach = shared.CASE_HEIGHT_MM - shared.PCB_TOP_Z_MM
        actuator = modeling.cylinder(
            f"Proxy_Button_Actuator_{index:02d}",
            shared.PANEL_BUTTON_ACTUATOR_DIAMETER_MM,
            reach,
            (x, y, shared.PCB_TOP_Z_MM + reach / 2.0),
            collection,
            vertices=16,
        )
        actuator.data.materials.append(palette["body"])

    module = modeling.rounded_box(
        "Proxy_Display_Module",
        shared.PANEL_OLED_MODULE_MM,
        (
            *shared.PANEL_OLED_CENTER_MM,
            shared.CASE_HEIGHT_MM
            - shared.TILE_PLATE_THICKNESS_MM
            - shared.PANEL_OLED_MODULE_MM[2] / 2.0
            + shared.PANEL_OLED_RECESS_DEPTH_MM,
        ),
        0.6,
        collection,
    )
    module.data.materials.append(palette["display"])
    module["purpose"] = "AZ-Delivery SH1106 OLED on a four-wire jumper"
