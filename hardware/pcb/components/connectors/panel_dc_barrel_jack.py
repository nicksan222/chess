"""Off-board assembly product: PanelDcBarrelJack.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import BARREL_JACK, ComponentSpec
from shared.electronics.barrel_jack import BarrelJackPin


@dataclass(frozen=True, slots=True)
class PanelDcBarrelJack:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = BARREL_JACK
    pin_type: ClassVar[type[BarrelJackPin]] = BarrelJackPin
