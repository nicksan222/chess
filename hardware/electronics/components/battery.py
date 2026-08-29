"""User-removable AA NiMH pack. Charging is deliberately external."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import POLARIZED, Component

BATTERY = Component(
    lib="BATTERY",
    value="6xAA NiMH",
    description="User-removable rechargeable NiMH pack",
    package="6xAA holder",
    build=lambda: elm.Battery().right(),
    pins=POLARIZED,
)
