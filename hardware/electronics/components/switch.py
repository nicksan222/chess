"""Latching power switch. The design uses one pole of a DPST rocker."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

SWITCH = Component(
    lib="SWITCH",
    value="POWER",
    description="Latching power switch; use one pole",
    package="DPST rocker",
    build=lambda: elm.Switch().right(),
    pins=TWO_TERMINAL,
)
