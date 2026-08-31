"""Momentary tactile switch for the control panel.

All twelve panel inputs are this one part, so there is a single line to buy and
a single motion to repeat twelve times. A 9.5 mm actuator reaches the case bezel
from the board without needing a separate cap.
"""

from __future__ import annotations

from schemdraw import elements as elm

from .base import TWO_TERMINAL, Component

BUTTON = Component(
    lib="BUTTON",
    value="TACT 6mm",
    description="Momentary panel button, 9.5 mm actuator",
    package="6x6 mm THT",
    build=lambda: elm.Button().right(),
    pins=TWO_TERMINAL,
)
