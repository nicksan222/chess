"""PCB specialization of the main latching rocker switch SW13."""

from domain.component import ComponentReference
from domain.footprint import Footprint, two_pad_axial
from shared.electronics.passives import PowerSwitchComponent, PowerSwitchPin


class PowerSwitch(PowerSwitchComponent):
    FOOTPRINT = two_pad_axial(
        "SPST rocker THT",
        "Latching rocker power switch",
        pitch=12.7,
        lead_diameter=1.2,
        body=(19.5, 13.0),
        pin_numbers=tuple(PowerSwitchPin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT


MAIN_POWER_SWITCH = PowerSwitch(ComponentReference.MAIN_POWER_SWITCH)
ROCKER_SWITCH = PowerSwitch.FOOTPRINT
