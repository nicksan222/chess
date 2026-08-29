"""Normally-open magnetic reed sensor, one per board square."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

REED = Component(
    lib="REED",
    value="REED NO",
    description="Normally-open magnetic sensor",
    package="axial 14 mm",
    build=lambda: elm.SwitchReed().right(),
    pins=TWO_TERMINAL,
)
