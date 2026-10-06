"""Off-board assembly product: PowerHarnessHousing4Pin.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import POWER_HARNESS_HOUSING, ComponentSpec


@dataclass(frozen=True, slots=True)
class PowerHarnessHousing4Pin:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = POWER_HARNESS_HOUSING
    cavity_numbers: ClassVar[tuple[int, ...]] = (1, 2, 3, 4)
