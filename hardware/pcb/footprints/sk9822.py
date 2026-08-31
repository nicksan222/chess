"""SK9822 in the 5050 package: the board's only surface-mount part.

Six pads on two sides, which is what distinguishes it from a WS2812B's four and
is the whole reason the chain needs no critical timing. Pads extend outward past
the body so a hand-soldered fillet is visible and inspectable from the side.

Numbering matches `hardware/pcb/components/sk9822.py`, which states the
convention it uses: 1 VDD, 2 GND, 3 SDI, 4 CKI, 5 SDO, 6 CKO.
"""

from __future__ import annotations

from .base import RECT, Footprint, Pad, courtyard_for

SUPPLY_PIN = "1"
GROUND_PIN = "2"
DATA_IN_PIN = "3"
CLOCK_IN_PIN = "4"
DATA_OUT_PIN = "5"
CLOCK_OUT_PIN = "6"
CHAIN_PINS = (DATA_IN_PIN, CLOCK_IN_PIN, DATA_OUT_PIN, CLOCK_OUT_PIN)

BODY_MM = (5.0, 5.0)
_PAD_LONG = 1.5
_PAD_SHORT = 1.0
_EDGE = 2.5
_PITCH = 1.6

_PADS = (
    # Left edge, top to bottom: data in, clock in.
    Pad(DATA_IN_PIN, -_EDGE, _PITCH / 2.0, _PAD_LONG, _PAD_SHORT, RECT),
    Pad(CLOCK_IN_PIN, -_EDGE, -_PITCH / 2.0, _PAD_LONG, _PAD_SHORT, RECT),
    # Right edge: data out, clock out.
    Pad(DATA_OUT_PIN, _EDGE, _PITCH / 2.0, _PAD_LONG, _PAD_SHORT, RECT),
    Pad(CLOCK_OUT_PIN, _EDGE, -_PITCH / 2.0, _PAD_LONG, _PAD_SHORT, RECT),
    # Supply above, ground below.
    Pad(SUPPLY_PIN, 0.0, _EDGE, _PAD_SHORT, _PAD_LONG, RECT),
    Pad(GROUND_PIN, 0.0, -_EDGE, _PAD_SHORT, _PAD_LONG, RECT),
)

SK9822_5050 = Footprint(
    package="PLCC-6 5050",
    description="SK9822 clocked addressable RGB LED",
    pads=_PADS,
    courtyard=courtyard_for(_PADS, BODY_MM),
)
