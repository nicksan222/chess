"""PCB specialization of the SN74AHCT125 level shifter."""

from base.component import ComponentReference
from base.footprint import Footprint, soic
from shared.electronics.ahct125 import Ahct125Component, Ahct125Pin


class Ahct125(Ahct125Component):
    """Own the U5 land pattern and dense-pin routing escape."""

    SIGNAL_ESCAPE_HORIZONTAL = True
    POWER_ESCAPE_MM = 1.2
    POWER_ESCAPE_HORIZONTAL = True
    FOOTPRINT = soic(
        "SOIC-14 1.27 mm",
        "SN74AHCT125DR narrow SOIC",
        14,
        5.40,
        (6.2, 8.7),
        tuple(Ahct125Pin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        return 2.0 + (int(pin_number) - 1) % 4


LED_LEVEL_SHIFTER = Ahct125(ComponentReference.LED_LEVEL_SHIFTER)
AHCT125_SOIC = Ahct125.FOOTPRINT
