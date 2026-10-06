"""Off-board assembly product: PanelPowerRockerSwitch.

This purchased part is not a pad on the main PCB. Unknown manufacturer body
sizes and terminal order remain unknown in the shared purchasing contract.
"""

from dataclasses import dataclass
from typing import ClassVar

from shared.components import POWER_SWITCH, ComponentSpec
from shared.electronics.passives import PowerSwitchPin


@dataclass(frozen=True, slots=True)
class PanelPowerRockerSwitch:
    """Identify one assembly instance and its approved purchasing facts."""

    reference: str
    product: ClassVar[ComponentSpec] = POWER_SWITCH
    pin_type: ClassVar[type[PowerSwitchPin]] = PowerSwitchPin
