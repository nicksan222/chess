"""Main latching power switch SW13."""

from enum import StrEnum

from base.component import BoardComponent, ComponentReference


class PowerSwitchPin(StrEnum):
    FUSED_INPUT = "1"
    SWITCHED_FIVE_VOLTS = "2"


class PowerSwitch(BoardComponent[PowerSwitchPin]):
    pin_type = PowerSwitchPin


MAIN_POWER_SWITCH = PowerSwitch(ComponentReference.MAIN_POWER_SWITCH)
