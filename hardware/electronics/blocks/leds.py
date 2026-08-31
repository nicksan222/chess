"""64 SK9822 LEDs as one clocked SPI shift register.

Because the part has its own clock line, the chain has no timing requirement:
a host that stalls between bytes latches late instead of corrupting the frame.
That is the whole reason the board needs no microcontroller to drive it.

Drawn in chain order rather than board order, eight to a row, so the sequence
reads like text: follow the pair of wires left to right, then down. Each LED
still carries its board square as a label, so the physical mapping is on the
sheet without dictating where the symbol sits.
"""

from __future__ import annotations

from components import CERAMIC_DISC, SK9822, capacitor
from components.sk9822 import (
    CLOCK_IN_PIN,
    CLOCK_OUT_PIN,
    DATA_IN_PIN,
    DATA_OUT_PIN,
    GND_PIN,
    VDD_PIN,
)
from core.canvas import Schematic
from core.names import (
    LED_CLOCK_END_NET,
    LED_CLOCK_NET,
    LED_DATA_END_NET,
    LED_DATA_NET,
    led_chain_order,
)

FIRST_LED = 6
FIRST_CAP = 8
PER_ROW = 8
PITCH_X = 18.0
PITCH_Y = 18.0
CAP_OFFSET_X = 9.0
CAP_OFFSET_Y = -8.0


def link_nets(link: int) -> tuple[str, str]:
    """Names for the pair of wires leaving LED number `link` (1-based)."""
    return (f"LED_D{link}", f"LED_C{link}")


def add_led_chain(
    sch: Schematic, *, origin_x: float = 0.0, origin_y: float = 0.0
) -> list[str]:
    chain = led_chain_order()
    refs: list[str] = []

    for index, (square_name, _file_index, _rank) in enumerate(chain):
        led = f"U{FIRST_LED + index}"
        refs.append(led)
        row, column = divmod(index, PER_ROW)
        x = origin_x + column * PITCH_X
        y = origin_y - row * PITCH_Y
        sch.place(
            SK9822,
            led,
            x,
            y,
            {"Square": square_name, "ChainIndex": str(index + 1)},
            {"Square"},
        )
        sch.place(
            capacitor(CERAMIC_DISC, "100nF", "Local LED decoupling capacitor"),
            f"C{FIRST_CAP + index}",
            x + CAP_OFFSET_X,
            y + CAP_OFFSET_Y,
            {"Square": square_name},
            {"Square"},
        )
        # Rail labels rather than wires: routing a cap back to the LED pins
        # would drag two wires straight through both parts' text.
        sch.label_pin("+5V", led, VDD_PIN)
        sch.label_pin("GND", led, GND_PIN)
        sch.label_pin("+5V", f"C{FIRST_CAP + index}", "1")
        sch.label_pin("GND", f"C{FIRST_CAP + index}", "2")

    sch.label_pin(LED_DATA_NET, refs[0], DATA_IN_PIN)
    sch.label_pin(LED_CLOCK_NET, refs[0], CLOCK_IN_PIN)

    for index in range(len(refs) - 1):
        source, target = refs[index], refs[index + 1]
        if index % PER_ROW != PER_ROW - 1:
            # Neighbours on the same row: both signals run straight across.
            sch.wire(*sch.pin(source, DATA_OUT_PIN), *sch.pin(target, DATA_IN_PIN))
            sch.wire(*sch.pin(source, CLOCK_OUT_PIN), *sch.pin(target, CLOCK_IN_PIN))
            continue
        # End of a row. A drawn wire would sweep back across every LED it
        # passes, so the turn is carried by name instead.
        data_net, clock_net = link_nets(index + 1)
        sch.label_pin(data_net, source, DATA_OUT_PIN)
        sch.label_pin(clock_net, source, CLOCK_OUT_PIN)
        sch.label_pin(data_net, target, DATA_IN_PIN)
        sch.label_pin(clock_net, target, CLOCK_IN_PIN)

    sch.label_pin(LED_DATA_END_NET, refs[-1], DATA_OUT_PIN)
    sch.label_pin(LED_CLOCK_END_NET, refs[-1], CLOCK_OUT_PIN)
    return refs
