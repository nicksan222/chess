"""KiCad footprint and approved PCB binding for power switch."""

from pcb.definition.parts.land_patterns import two_pad_axial
from pcb.definition.parts.part import PcbPart
from shared.components import POWER_SWITCH
from shared.electronics import ComponentReference
from shared.electronics.passives import PowerSwitchComponent as PowerSwitch
from shared.electronics.passives import PowerSwitchPin

POWERSWITCH_FOOTPRINT = two_pad_axial(
    "SPST rocker THT",
    "Latching rocker power switch",
    pitch=12.7,
    lead_diameter=1.2,
    body=(19.5, 13.0),
    pin_numbers=tuple(PowerSwitchPin),
)

POWER_SWITCH_PART = PcbPart(
    POWER_SWITCH,
    PowerSwitch,
    POWERSWITCH_FOOTPRINT,
    "SWITCH",
    "POWER",
    "Latching power switch",
)

MAIN_POWER_SWITCH = PowerSwitch(ComponentReference.MAIN_POWER_SWITCH)
