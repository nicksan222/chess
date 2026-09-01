"""Pin headers: the Raspberry Pi socket and the display connector."""

from __future__ import annotations

from base.footprint import pin_header
from components.oled_header import OledHeaderPin
from components.raspberry_pi_header import RaspberryPiHeaderPin

# Two rows of twenty, numbered odd on one row and even on the other, matching
# every published Raspberry Pi pinout. The Pi hangs underneath, but the pads are
# the same either way.
PI_HEADER = pin_header(
    "2x20 2.54 mm THT",
    "Raspberry Pi Zero 2 W GPIO socket",
    columns=20,
    rows=2,
    pin_numbers=tuple(RaspberryPiHeaderPin),
)

OLED_HEADER = pin_header(
    "1x4 2.54 mm THT",
    "Four-pin SH1106 I2C OLED module connector",
    columns=4,
    rows=1,
    pin_numbers=tuple(OledHeaderPin),
)
