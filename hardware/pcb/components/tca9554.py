"""PCB specialization of the TI TCA9554DWR GPIO expander."""

from base.footprint import Footprint, soic
from shared.electronics.tca9554 import Tca9554Component, Tca9554Pin


class Tca9554(Tca9554Component):
    """Own the TI DW0016A land pattern and its staggered signal escape."""

    SIGNAL_ESCAPE_HORIZONTAL = True
    POWER_ESCAPE_HORIZONTAL = True
    FOOTPRINT = soic(
        "SOIC-16W 1.27 mm",
        "TCA9554DWR wide SOIC, TI DW0016A",
        16,
        9.30,
        (7.6, 10.5),
        tuple(Tca9554Pin),
        pad_size_mm=(2.0, 0.60),
    )
    BYPASS_OFFSET_MM = (8.0, 6.0)
    SILKSCREEN_CLEARANCE_MM = 2.0

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        return 2.0 + (int(pin_number) - 1) % 4


TCA9554_SOIC = Tca9554.FOOTPRINT
