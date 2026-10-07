"""Off-board assembly product: HostGpioMaleHeader40Pin.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import PI_MALE_HEADER, ComponentSpec
from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin


@dataclass(frozen=True, slots=True)
class HostGpioMaleHeader40Pin:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = PI_MALE_HEADER
    pin_type: ClassVar[type[RaspberryPiHeaderPin]] = RaspberryPiHeaderPin
