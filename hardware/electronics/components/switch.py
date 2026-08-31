"""Latching power switch in the 5 V input, on the rear wall of the case."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

SWITCH = Component(
    lib="SWITCH",
    value="POWER",
    description="Latching power switch",
    package="SPST rocker THT",
    build=lambda: elm.Switch().right(),
    pins=TWO_TERMINAL,
)
