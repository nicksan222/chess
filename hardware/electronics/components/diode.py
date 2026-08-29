"""Small-signal isolation diode that stops matrix ghosting."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import POLARIZED, Component

DIODE = Component(
    lib="DIODE",
    value="1N4148W",
    description="Matrix isolation diode",
    package="SOD-123",
    build=lambda: elm.Diode().right(),
    pins=POLARIZED,
)
