"""Off-board assembly product: RockerSwitchReceptacle.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import ROCKER_RECEPTACLE, ComponentSpec


@dataclass(frozen=True, slots=True)
class RockerSwitchReceptacle:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = ROCKER_RECEPTACLE
    wire_gauge_awg: ClassVar[tuple[int, int]] = (22, 18)
