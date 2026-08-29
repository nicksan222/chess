"""74AHCT1G125 buffer: reads 3.3 V logic, drives a valid 5 V LED data line."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit


def _build() -> elm.Ic:
    return integrated_circuit(
        [
            elm.IcPin(name="OE", pin="1", side="left", anchorname="1"),
            elm.IcPin(name="A", pin="2", side="left", anchorname="2"),
            elm.IcPin(name="GND", pin="3", side="bottom", anchorname="3"),
            elm.IcPin(name="Y", pin="4", side="right", anchorname="4"),
            elm.IcPin(name="VCC", pin="5", side="top", anchorname="5"),
        ],
        "74AHCT1G125",
        pinspacing=1.2,
    )


AHCT125 = Component(
    lib="AHCT125",
    value="74AHCT1G125",
    description="5 V AHCT buffer accepts 3.3 V LED data",
    package="SOT-23-5",
    build=_build,
    pins=BY_PIN_NUMBER,
)
