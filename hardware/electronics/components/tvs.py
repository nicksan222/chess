"""Transient suppressor across the 5 V input.

It clamps a spike, and on a reverse-polarity or over-voltage supply it conducts
hard enough to open the fuse rather than letting the mistake reach the Pi. That
pairing is why the board needs no series protection diode, which at four amps
would have to dissipate watts.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import POLARIZED, Component

TVS = Component(
    lib="TVS",
    value="P6KE6.8A",
    description="Input transient suppressor on the 5 V rail",
    package="axial DO-15",
    # Drawn upward so the cathode lands on the rail it protects and the anode
    # falls to ground, the way a shunt clamp is normally shown.
    build=lambda: elm.DiodeTVS().up(),
    pins=POLARIZED,
)
