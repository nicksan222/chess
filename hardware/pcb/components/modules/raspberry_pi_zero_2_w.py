"""Off-board assembly product: RaspberryPiZero2W.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import PI_ZERO_2_W, ComponentSpec
from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin


@dataclass(frozen=True, slots=True)
class RaspberryPiZero2W:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = PI_ZERO_2_W
    header_pin_type: ClassVar[type[RaspberryPiHeaderPin]] = RaspberryPiHeaderPin
