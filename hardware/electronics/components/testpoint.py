"""Bring-up probe points.

One turret type for every probe, so the board adds a single line to the order
rather than one per pad size.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import SINGLE, Component

TESTPOINT_TURRET = Component(
    lib="TESTPOINT",
    value="",
    description="Turret test point",
    package="turret 1.6 mm THT",
    build=lambda: elm.Dot(open=True),
    pins=SINGLE,
    part="Turret test point",
)


def testpoint(value: str, description: str) -> Component:
    return TESTPOINT_TURRET.variant(value, description)
