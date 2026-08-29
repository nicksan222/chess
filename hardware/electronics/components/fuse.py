"""Input over-current protection."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

FUSE = Component(
    lib="FUSE",
    value="5 A",
    description="Input over-current protection",
    package="mini blade",
    build=lambda: elm.Fuse().right(),
    pins=TWO_TERMINAL,
)
