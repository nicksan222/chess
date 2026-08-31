"""64 reed switches read directly, sixteen per I2C expander.

There is no matrix here. Every reed gets its own input pin, which removes the
64 isolation diodes a scanned matrix needs, removes ghosting as a concept, and
removes scan timing from the host's job. The expanders interrupt on change, so
the Pi reads eight bytes only when a piece actually moves.

Contacts pull to ground against the expander's internal pull-up. Their bounce is
handled by the host's settle window rather than by 128 more components.
"""

from __future__ import annotations

from components import (
    CERAMIC_DISC,
    I2C_EXPANDER,
    REED,
    SOCKET_DIP28,
    capacitor,
)
from components.i2c_expander import (
    ADDRESS_PINS,
    INTA_PIN,
    INTB_PIN,
    PORT_PINS,
    RESET_PIN,
    SCL_PIN,
    SDA_PIN,
    UNUSED_PINS,
    VDD_PIN,
    VSS_PIN,
)
from core.canvas import Schematic
from core.names import (
    EXPANDER_COUNT,
    SCL_NET,
    SDA_NET,
    SENSE_IRQ_NET,
    expander_address,
    expander_quadrant,
    expander_squares,
    expander_straps,
    sense_net,
)

REED_COLUMNS = 2
REED_ROWS = 8
REED_ROW_PITCH = 4.0
REED_COLUMN_PITCH = 17.0
REED_OFFSET_X = 24.0
SOCKET_OFFSET_Y = -24.0
QUADRANT_PITCH_X = 64.0
QUADRANT_PITCH_Y = 56.0


def add_sensing(
    sch: Schematic, *, origin_x: float = 0.0, origin_y: float = 0.0
) -> None:
    for index in range(EXPANDER_COUNT):
        quadrant_x = origin_x + (index % 2) * QUADRANT_PITCH_X
        quadrant_y = origin_y + (index // 2) * QUADRANT_PITCH_Y
        _add_quadrant(sch, index, quadrant_x, quadrant_y)


def _add_quadrant(sch: Schematic, index: int, x: float, y: float) -> None:
    expander = f"U{index + 1}"
    sch.place(
        I2C_EXPANDER,
        expander,
        x,
        y,
        {"Quadrant": expander_quadrant(index), "Address": f"0x{expander_address(index):02X}"},
    )
    sch.place(SOCKET_DIP28, f"SKT{index + 1}", x, y + SOCKET_OFFSET_Y)
    sch.place(
        capacitor(CERAMIC_DISC, "100nF", "Expander decoupling capacitor"),
        f"C{3 + index}",
        x + 12.0,
        y + SOCKET_OFFSET_Y + 2.0,
    )

    for ref, pin, net in (
        (expander, VDD_PIN, "+3V3"),
        (expander, VSS_PIN, "GND"),
        (expander, SDA_PIN, SDA_NET),
        (expander, SCL_PIN, SCL_NET),
        (expander, RESET_PIN, "+3V3"),
        (expander, INTA_PIN, SENSE_IRQ_NET),
        (f"C{3 + index}", "1", "+3V3"),
        (f"C{3 + index}", "2", "GND"),
    ):
        sch.label_pin(net, ref, pin)

    # A2 is grounded on every device; A1 and A0 encode the quadrant, which is
    # what makes the four addresses consecutive from 0x20.
    for strap_pin, high in zip(ADDRESS_PINS, expander_straps(index)):
        sch.label_pin("+3V3" if high else "GND", expander, strap_pin)

    # Port B interrupts duplicate port A on a wired-OR line, so only INTA is used.
    sch.nc(*sch.pin(expander, INTB_PIN))
    for pin in UNUSED_PINS:
        sch.nc(*sch.pin(expander, pin))

    reed_base = index * 16
    for pin_index, square_name in expander_squares(index):
        reed = f"RS{reed_base + pin_index + 1}"
        column, row = divmod(pin_index, REED_ROWS)
        reed_x = x + REED_OFFSET_X + column * REED_COLUMN_PITCH
        reed_y = y + (REED_ROWS - 1) * REED_ROW_PITCH / 2.0 - row * REED_ROW_PITCH
        sch.place(REED, reed, reed_x, reed_y, {"Square": square_name}, {"Square"})
        # Named rather than drawn: sixteen wires from a column of reeds back
        # across the expander body would bury the symbol they connect to.
        sch.label_pin(sense_net(square_name), reed, "1")
        sch.label_pin("GND", reed, "2")
        sch.label_pin(sense_net(square_name), expander, PORT_PINS[pin_index])
