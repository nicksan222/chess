"""The face-up control strip: twelve buttons and the display connector.

All twelve inputs are the same tactile switch on a plain Broadcom line, so
remapping one is a host-software change and adding one costs a trace. Nothing
here goes through an expander.

The display is an SSD1306 OLED on a four-pin header. It runs at 3.3 V like the
Pi, which is why the board needs no I2C level translation: a 5 V character
module would have put 5 V pull-ups straight onto the Pi's bus.
"""

from __future__ import annotations

from components import BUTTON, OLED_HEADER
from components.oled_header import GND_PIN, SCL_PIN, SDA_PIN, SUPPLY_PIN
from core.canvas import Schematic
from core.names import (
    BUTTON_NAMES,
    OLED_ADDRESS,
    SCL_NET,
    SDA_NET,
    button_net,
)

PER_COLUMN = 6
COLUMN_PITCH = 20.0
ROW_PITCH = 5.0


def add_control_panel(
    sch: Schematic, *, origin_x: float = 0.0, origin_y: float = 0.0
) -> None:
    for index, name in enumerate(BUTTON_NAMES):
        column, row = divmod(index, PER_COLUMN)
        sch.place(
            BUTTON,
            f"SW{index + 1}",
            origin_x + column * COLUMN_PITCH,
            origin_y - row * ROW_PITCH,
            {"Function": name},
            {"Function"},
        )
        sch.label_pin(button_net(name), f"SW{index + 1}", "1")
        sch.label_pin("GND", f"SW{index + 1}", "2")

    display_x = origin_x + 2 * COLUMN_PITCH + 8.0
    sch.place(OLED_HEADER, "J2", display_x, origin_y - 4.0)
    for pin, net in (
        (GND_PIN, "GND"),
        (SUPPLY_PIN, "+3V3"),
        (SCL_PIN, SCL_NET),
        (SDA_PIN, SDA_NET),
    ):
        sch.label_pin(net, "J2", pin)

    sch.note(
        f"Buttons pull to ground against the Pi's internal pull-ups. "
        f"Display answers at 0x{OLED_ADDRESS:02X}.",
        origin_x - 2.0,
        origin_y - PER_COLUMN * ROW_PITCH - 3.0,
    )
