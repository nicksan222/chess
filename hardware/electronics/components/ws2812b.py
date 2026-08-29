"""Addressable RGB LED, one per board square.

Supply on top and ground underneath, data straight through left to right, so
the rail symbols never cross the serpentine data wire.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit


def _build() -> elm.Ic:
    return integrated_circuit(
        [
            elm.IcPin(name="VDD", pin="1", side="top", anchorname="1"),
            elm.IcPin(name="DIN", pin="4", side="left", anchorname="4"),
            elm.IcPin(name="DOUT", pin="2", side="right", anchorname="2"),
            elm.IcPin(name="GND", pin="3", side="bottom", anchorname="3"),
        ],
        "WS2812B",
        pinspacing=1.2,
    )


WS2812B = Component(
    lib="WS2812B",
    value="WS2812B",
    description="Addressable RGB LED",
    package="PLCC-4 5 mm",
    build=_build,
    pins=BY_PIN_NUMBER,
)
