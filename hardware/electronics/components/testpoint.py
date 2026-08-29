"""Bring-up probe points."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import SINGLE, Component

TESTPOINT_LOOP = Component(
    lib="TESTPOINT",
    value="",
    description="Loop test point",
    package="D2.6 mm",
    build=lambda: elm.Dot(open=True),
    pins=SINGLE,
    part="Loop test point",
)
TESTPOINT_PAD = Component(
    lib="TESTPOINT",
    value="",
    description="Pad test point",
    package="D1.5 mm",
    build=lambda: elm.Dot(open=True),
    pins=SINGLE,
    part="Pad test point",
)


def testpoint(template: Component, value: str, description: str) -> Component:
    return template.variant(value, description)
