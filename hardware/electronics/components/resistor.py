"""Through-hole resistor. Every use supplies its own value and reason."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

RESISTOR = Component(
    lib="R",
    value="",
    description="Through-hole resistor",
    package="axial 1/4 W",
    build=lambda: elm.Resistor().right(),
    pins=TWO_TERMINAL,
)


def resistor(value: str, description: str) -> Component:
    return RESISTOR.variant(value, description)
