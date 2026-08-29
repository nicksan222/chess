"""Ceramic and electrolytic capacitors."""

from __future__ import annotations

from dataclasses import replace

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

CERAMIC_0603 = Component(
    lib="C",
    value="100nF",
    description="Ceramic capacitor",
    package="0603",
    build=lambda: elm.Capacitor().down().length(2.0),
    pins=TWO_TERMINAL,
)
CERAMIC_0805 = replace(CERAMIC_0603, value="10uF", package="0805")

ELECTROLYTIC_8X10 = Component(
    lib="C",
    value="220uF 16V",
    description="Low-ESR electrolytic",
    package="8x10",
    build=lambda: elm.Capacitor(polar=True).down().length(2.0),
    pins=TWO_TERMINAL,
)
ELECTROLYTIC_10X10 = replace(ELECTROLYTIC_8X10, value="1000uF 10V", package="10x10")


def capacitor(template: Component, value: str, description: str) -> Component:
    return template.variant(value, description)
