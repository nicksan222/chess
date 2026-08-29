"""Input transient suppressor on the raw battery rail."""

from __future__ import annotations

from schemdraw import elements as elm

from .base import POLARIZED, Component

TVS = Component(
    lib="TVS",
    value="SMBJ12A",
    description="Input transient suppressor",
    package="SMB",
    # Drawn upward so the cathode lands on the rail it protects and the anode
    # falls to ground, the way a shunt clamp is normally shown.
    build=lambda: elm.DiodeTVS().up(),
    pins=POLARIZED,
)
