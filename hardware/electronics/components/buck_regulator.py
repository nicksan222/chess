"""Pololu D36V50F5 step-down module producing the 5 V controller and LED rail."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import BY_PIN_NUMBER, Component, integrated_circuit


def _build() -> elm.Ic:
    return integrated_circuit(
        [
            elm.IcPin(name="VIN", pin="1", side="left", anchorname="1"),
            elm.IcPin(name="GND", pin="2", side="bottom", anchorname="2"),
            elm.IcPin(name="VOUT", pin="3", side="right", anchorname="3"),
            elm.IcPin(name="EN", pin="4", side="top", anchorname="4"),
        ],
        "D36V50F5",
        pinspacing=1.3,
    )


BUCK_5V_5A = Component(
    lib="BUCK_5V_5A",
    value="D36V50F5",
    description="5 V, 5 A step-down regulator module",
    package="Pololu D36V50F5",
    build=_build,
    pins=BY_PIN_NUMBER,
)
