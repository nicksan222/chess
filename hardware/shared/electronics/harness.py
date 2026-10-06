"""The off-board wiring harnesses: one definition for tests, BOM and assembly.

Each wire is fixed by the connector cavity it is crimped into. A JST cavity mates
the header circuit of the same number, counted the way JST's drawings count them
(VH catalogue p4, SH catalogue p1), so physical cavity k lands on board pad k only
while the footprint keeps the drawing's chirality (pcb tests/board/test_harness).
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.components import (
    COMPONENTS,
    OLED_HARNESS_WIRES,
    POWER_HARNESS_WIRES,
    ComponentSpec,
)
from shared.components.harness import OLED_WIRE_LENGTH_MM, POWER_WIRE_LENGTH_MM

from .barrel_jack import BarrelJackPin
from .connectors import OledHeaderPin
from .passives import PowerSwitchPin
from .power_header import PowerHeaderPin


@dataclass(frozen=True)
class HarnessWire:
    """One wire of a harness, fixed by the connector cavity it is crimped into, with its net, colour, gauge, length and far end."""

    connector: str  # Board reference of the header the housing plugs into.
    cavity: str  # JST cavity number == header circuit number it mates.
    net: str  # Board net that circuit must carry.
    colour: str
    gauge_awg: int
    length_mm: float
    far_part: str  # Component key at the far end.
    far_terminal: str  # Terminal name there, as the part's drawing labels it.
    far_termination: str  # How the wire is attached at the far end.

    @property
    def wire(self) -> ComponentSpec:
        """The bought wire of this gauge and colour (one BOM line per colour)."""
        return {18: POWER_HARNESS_WIRES, 28: OLED_HARNESS_WIRES}[self.gauge_awg][
            self.colour
        ]
