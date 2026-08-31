"""DC barrel jack, the board's only power input.

A 5 V brick feeds the rail directly, so the board carries no regulator at all:
no buck converter, no inductor, no USB power negotiation. Centre positive.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit

TIP_PIN = "1"
SLEEVE_PIN = "2"


def _build() -> elm.Ic:
    return integrated_circuit(
        [
            elm.IcPin(name="TIP", pin=TIP_PIN, side="right", anchorname=TIP_PIN),
            elm.IcPin(
                name="SLEEVE", pin=SLEEVE_PIN, side="bottom", anchorname=SLEEVE_PIN
            ),
        ],
        "DC 5 V IN",
        pinspacing=1.6,
    )


BARREL_JACK = Component(
    lib="BARREL_JACK",
    value="DC 5.5x2.1",
    description="5 V DC input jack, centre positive",
    package="5.5x2.1 mm THT",
    build=_build,
    pins=BY_PIN_NUMBER,
)
