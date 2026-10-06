"""Off-board assembly product: OledDisplayModule.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import OLED_MODULE, ComponentSpec


@dataclass(frozen=True, slots=True)
class OledDisplayModule:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = OLED_MODULE
    # Labelled pads only; their physical order has not been verified.
    terminal_labels: ClassVar[tuple[str, ...]] = ("GND", "VCC", "SCL", "SDA")
