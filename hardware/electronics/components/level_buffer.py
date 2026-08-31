"""SN74AHCT125N quad buffer in DIP-14, translating 3.3 V SPI to 5 V.

SK9822 needs roughly 0.7 x VDD for a valid logic high, so 3.5 V at a 5 V
supply, and the Pi drives 3.3 V. An AHCT input threshold is TTL-compatible, so
one buffer stage per SPI signal produces a clean 5 V clock and data line. Two of
the four channels carry the chain; the other two are tied off.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit

VCC_PIN = "14"
GND_PIN = "7"
# One tuple per channel: output enable, input, output. OE is active low.
CHANNELS = (
    ("1", "2", "3"),
    ("4", "5", "6"),
    ("10", "9", "8"),
    ("13", "12", "11"),
)
USED_CHANNELS = CHANNELS[:2]
SPARE_CHANNELS = CHANNELS[2:]

PIN_NAMES = {VCC_PIN: "VCC", GND_PIN: "GND"}
for _index, (_oe, _a, _y) in enumerate(CHANNELS, start=1):
    PIN_NAMES[_oe] = f"{_index}OE"
    PIN_NAMES[_a] = f"{_index}A"
    PIN_NAMES[_y] = f"{_index}Y"

LEFT_PINS = tuple(pin for oe, a, _y in CHANNELS for pin in (oe, a))
RIGHT_PINS = (*(y for _oe, _a, y in CHANNELS), VCC_PIN, GND_PIN)


def _build() -> elm.Ic:
    left = [
        elm.IcPin(name=PIN_NAMES[pin], pin=pin, side="left", anchorname=pin)
        for pin in LEFT_PINS
    ]
    right = [
        elm.IcPin(name=PIN_NAMES[pin], pin=pin, side="right", anchorname=pin)
        for pin in RIGHT_PINS
    ]
    return integrated_circuit(left + right, "SN74AHCT125N", pinspacing=1.9)


LEVEL_BUFFER = Component(
    lib="AHCT125",
    value="SN74AHCT125N",
    description="Quad 5 V buffer accepts 3.3 V SPI clock and data",
    package="DIP-14",
    build=_build,
    pins=BY_PIN_NUMBER,
)
