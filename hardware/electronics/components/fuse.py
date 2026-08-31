"""Input over-current protection, in a holder so it can be replaced."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

FUSE = Component(
    lib="FUSE",
    value="5 A",
    description="Input over-current protection",
    package="5x20 mm holder THT",
    build=lambda: elm.Fuse().right(),
    pins=TWO_TERMINAL,
)
