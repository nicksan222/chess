"""Off-board assembly product: MicroSdCard32Gigabyte.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import MICRO_SD, ComponentSpec


@dataclass(frozen=True, slots=True)
class MicroSdCard32Gigabyte:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = MICRO_SD
    capacity_gigabytes: ClassVar[int] = 32
