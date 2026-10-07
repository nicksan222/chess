"""Off-board assembly product: OledHarnessCrimpContact.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import OLED_HARNESS_CONTACT, ComponentSpec


@dataclass(frozen=True, slots=True)
class OledHarnessCrimpContact:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = OLED_HARNESS_CONTACT
    wire_gauge_awg: ClassVar[tuple[int, int]] = (32, 28)
