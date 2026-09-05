"""PCB specialization of the four-pin I2C OLED connector J2."""

from base.component import ComponentReference
from base.footprint import Footprint, pin_header
from shared.electronics.connectors import OledHeaderComponent, OledHeaderPin


class OledHeader(OledHeaderComponent):
    FOOTPRINT = pin_header(
        "1x4 2.54 mm THT",
        "Four-pin SH1106 I2C OLED module connector",
        columns=4,
        rows=1,
        pin_numbers=tuple(OledHeaderPin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT


DISPLAY_HEADER = OledHeader(ComponentReference.DISPLAY_HEADER)
OLED_HEADER = OledHeader.FOOTPRINT
