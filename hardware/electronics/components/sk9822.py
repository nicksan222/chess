"""SK9822 addressable RGB LED, one per board square.

Unlike a WS2812B, this part carries a separate clock line, so the chain is an
ordinary SPI shift register with no timing requirement at all. A host that
stalls mid-frame simply latches late instead of corrupting the frame, which is
what makes driving the board straight from Linux user space safe.

Supply on top and ground underneath, clock and data straight through left to
right, so the rail symbols never cross the serpentine chain wires. Pin numbers
follow the module's own convention; the footprint assignment happens at layout.
"""

from __future__ import annotations

from schemdraw import elements as elm
from shared.components import SK9822 as SPEC

from .base import BY_PIN_NUMBER, Component, integrated_circuit

VDD_PIN = "1"
GND_PIN = "2"
DATA_IN_PIN = "3"
CLOCK_IN_PIN = "4"
DATA_OUT_PIN = "5"
CLOCK_OUT_PIN = "6"


def _build() -> elm.Ic:
    return integrated_circuit(
        [
            elm.IcPin(name="VDD", pin=VDD_PIN, side="top", anchorname=VDD_PIN),
            elm.IcPin(name="SDI", pin=DATA_IN_PIN, side="left", anchorname=DATA_IN_PIN),
            elm.IcPin(
                name="CKI", pin=CLOCK_IN_PIN, side="left", anchorname=CLOCK_IN_PIN
            ),
            elm.IcPin(
                name="SDO", pin=DATA_OUT_PIN, side="right", anchorname=DATA_OUT_PIN
            ),
            elm.IcPin(
                name="CKO", pin=CLOCK_OUT_PIN, side="right", anchorname=CLOCK_OUT_PIN
            ),
            elm.IcPin(name="GND", pin=GND_PIN, side="bottom", anchorname=GND_PIN),
        ],
        "SK9822",
        pinspacing=1.4,
    )


SK9822 = Component(
    lib=SPEC.key,
    value=SPEC.key,
    description=SPEC.description,
    package=SPEC.package,
    build=_build,
    pins=BY_PIN_NUMBER,
    spec=SPEC,
)
