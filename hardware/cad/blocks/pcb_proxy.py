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

# Same body size and positions the PCB placement uses, so the proxy shows the real
# obstruction the plate and case must clear.
EXPANDER_BODY_MM = shared.EXPANDER_BODY_MM
EXPANDER_POSITIONS_MM = tuple(shared.EXPANDER_POSITIONS_BY_BANK_MM.values())


def create_materials() -> dict[str, bpy.types.Material]:
    """Flat presentation colours keyed by role; they are not specified finishes."""
    return {
        "pcb": materials.solid("Circuit board", (0.02, 0.16, 0.07, 1.0), 0.38),
        "body": materials.solid("Component body", (0.10, 0.10, 0.11, 1.0), 0.34),
        "emitter": materials.solid("RGB emitter window", (0.78, 0.86, 0.92, 1.0), 0.10),
        "host": materials.solid("Raspberry Pi board", (0.16, 0.05, 0.10, 1.0), 0.42),
        "display": materials.solid("OLED glass", (0.02, 0.02, 0.03, 1.0), 0.08),
    }


def add_board(collection: bpy.types.Collection) -> bpy.types.Object:
    """The board itself, plus everything standing on it.

    Returns the board slab. The named `Proxy_*` objects (board, Pi, header, display,
    buttons and actuators) are what `board-assembly`'s `check_fit` tests against the
    printed parts; LEDs, Hall sensors and expanders are shown but covered by the shared stack
    validation instead.
    """
    palette = create_materials()

    # Board slab at its place in the stack: top face PCB_TOP_Z, thickness PCB_THICKNESS,
    # centred on the board (not the playing area), so the control strip is included.
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
    # LED body on the board top plus a thin emitter window on its top face, at the
    # shared LED offset, so the diffuser pockets in the plate can be seen to line up.
    height = shared.LED_PACKAGE_NOMINAL_SIZE_MM[2]
    for square in shared.BOARD_SQUARES:
        x, y = square.led_position_mm
        led = modeling.rounded_box(
            f"Proxy_LED_{square.row:02d}_{square.column:02d}",
            shared.LED_PACKAGE_NOMINAL_SIZE_MM,
            (x, y, shared.PCB_TOP_Z_MM + height / 2.0),
            0.3,
            collection,
        )
        led.data.materials.append(palette["body"])
        led["reference"] = shared.LED_PACKAGE_REFERENCE
        emitter = modeling.rounded_box(
            f"Proxy_LED_Window_{square.row:02d}_{square.column:02d}",
            (*shared.LED_EMITTER_WINDOW_MM, 0.2),
            (x, y, shared.PCB_TOP_Z_MM + height),
            0.0,
            collection,
        )
        emitter.data.materials.append(palette["emitter"])


def _add_hall_sensors(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    # One sensor body per square at the Hall position (square centre).
    height = shared.HALL_SENSOR_HEIGHT_MM
    for square in shared.BOARD_SQUARES:
        x, y = square.hall_position_mm
        sensor = modeling.rounded_box(
            f"Proxy_Hall_{square.row:02d}_{square.column:02d}",
            (*shared.HALL_SENSOR_BODY_MM, height),
            (x, y, shared.PCB_TOP_Z_MM + height / 2.0),
            0.2,
            collection,
        )
        sensor.data.materials.append(palette["body"])


def _add_expanders(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    # One TCA9554 per Hall bank, at the shared expander positions.
    for index, (x, y) in enumerate(EXPANDER_POSITIONS_MM):
        chip = modeling.rounded_box(
            f"Proxy_Expander_{index}",
            EXPANDER_BODY_MM,
            (x, y, shared.PCB_TOP_Z_MM + EXPANDER_BODY_MM[2] / 2.0),
            0.4,
            collection,
        )
        chip.data.materials.append(palette["body"])
        chip["purpose"] = "SMD TCA9554, one per compact 2x4 Hall bank"


def _add_host(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    """The Pi hangs under the board on its header, in the cavity.

    It sits at the shared Pi transform, the same one J1 is placed from, so a
    header pin here lands on the J1 pad above it.
    """
    top = shared.PI_TOP_FACE_Z_MM
    # A quarter-turn placement swaps the X and Y extents of the Pi and its header body.
    turned = int(shared.PI_ROTATION_DEG) % 180 == 90
    length, width, thickness = shared.PI_BOARD_SIZE_MM
    pi_board = modeling.rounded_box(
        "Proxy_Raspberry_Pi",
        (width, length, thickness) if turned else (length, width, thickness),
        (*shared.PI_CENTER_MM, top - thickness / 2.0),
        0.5,
        collection,
    )
    pi_board.data.materials.append(palette["host"])
    pi_board["purpose"] = "Raspberry Pi Zero 2 W; the only processor on the board"

    header_x, header_y, _ = shared.PI_HEADER_BODY_MM
    header = modeling.rounded_box(
        "Proxy_Pi_Header",
        (
            header_y if turned else header_x,
            header_x if turned else header_y,
            shared.PI_BOARD_TO_BOARD_MM,
        ),
        (*shared.PI_HEADER_CENTER_MM, top + shared.PI_BOARD_TO_BOARD_MM / 2.0),
        0.4,
        collection,
    )
    header.data.materials.append(palette["body"])


def _add_panel(
    collection: bpy.types.Collection, palette: dict[str, bpy.types.Material]
) -> None:
    # Buttons: housing (body) plus the round stem (actuator) up to the switch's overall
    # height. `check_fit` tests both against the plate, which has a hole and relief.
    for index, button in enumerate(shared.PANEL_BUTTONS):
        x, y = button.position_mm
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
        # The approved switch's overall height sets where the stem ends; the
        # shared validation keeps that just proud of the bezel.
        actuator = modeling.cylinder_between(
            f"Proxy_Button_Actuator_{index:02d}",
            shared.PANEL_BUTTON_ACTUATOR_DIAMETER_MM,
            (x, y),
            shared.PCB_TOP_Z_MM + shared.PANEL_BUTTON_BODY_MM[2],
            shared.PCB_TOP_Z_MM + shared.PANEL_BUTTON_HEIGHT_MM,
            collection,
            vertices=16,
        )
        actuator.data.materials.append(palette["body"])

    # The OLED module hangs from the plate underside in its recess, not on the PCB; its
    # top is raised by the recess depth so it sits inside the plate recess.
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
    module["purpose"] = "AZ-Delivery SSD1306 OLED on a four-wire jumper"
