"""Normally-open magnetic reed sensor, one per board square."""

from __future__ import annotations

from schemdraw import elements as elm
from shared.components import REED_SWITCH as SPEC

from .base import TWO_TERMINAL, Component

REED = Component(
    lib="REED",
    value="REED NO",
    description=SPEC.description,
    package=SPEC.package,
    build=lambda: elm.SwitchReed().right(),
    pins=TWO_TERMINAL,
    spec=SPEC,
)
