"""PCB specialization of the Raspberry Pi 40-pin GPIO header."""

from base.component import ComponentReference
from base.footprint import Footprint, pin_header
from shared.electronics.raspberry_pi_header import (
    HeaderLegend,
    HeaderLegendEntry,
    RaspberryPiHeaderComponent,
    RaspberryPiHeaderPin,
)


class RaspberryPiHeader(RaspberryPiHeaderComponent):
    """Own the socket geometry and launch-channel keepout dimensions."""

    FOOTPRINT = pin_header(
        "2x20 2.54 mm THT",
        "Raspberry Pi Zero 2 W GPIO socket",
        columns=20,
        rows=2,
        pin_numbers=tuple(RaspberryPiHeaderPin),
    )
    BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM = 1.2
    POWER_ESCAPE_MM = 6.0
    BUTTON_VIA_KEEPOUT_LENGTH_MM = 6.0

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT


HOST_GPIO_HEADER = RaspberryPiHeader(ComponentReference.HOST_GPIO_HEADER)
PI_HEADER = RaspberryPiHeader.FOOTPRINT

__all__ = (
    "HOST_GPIO_HEADER",
    "PI_HEADER",
    "HeaderLegend",
    "HeaderLegendEntry",
    "RaspberryPiHeader",
    "RaspberryPiHeaderPin",
)
