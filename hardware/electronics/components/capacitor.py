"""Through-hole ceramic and electrolytic capacitors.

Leaded parts throughout: nothing on this board is smaller than the fingers
assembling it, apart from the LEDs.
"""

from __future__ import annotations

from dataclasses import replace

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

CERAMIC_DISC = Component(
    lib="C",
    value="100nF",
    description="Ceramic capacitor",
    package="disc 2.54 mm",
    build=lambda: elm.Capacitor().down().length(2.0),
    pins=TWO_TERMINAL,
)

ELECTROLYTIC_RADIAL = Component(
    lib="C",
    value="1000uF 10V",
    description="Low-ESR electrolytic",
    package="radial 10 mm",
    build=lambda: elm.Capacitor(polar=True).down().length(2.0),
    pins=TWO_TERMINAL,
)
ELECTROLYTIC_SMALL = replace(ELECTROLYTIC_RADIAL, value="10uF 16V", package="radial 5 mm")


def capacitor(template: Component, value: str, description: str) -> Component:
    return template.variant(value, description)
