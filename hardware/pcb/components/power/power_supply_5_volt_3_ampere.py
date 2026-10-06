"""Off-board assembly product: PowerSupply5Volt3Ampere.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import POWER_SUPPLY, ComponentSpec


@dataclass(frozen=True, slots=True)
class PowerSupply5Volt3Ampere:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = POWER_SUPPLY
    output_volts: ClassVar[float] = 5.0
    rated_amperes: ClassVar[float] = 3.0
