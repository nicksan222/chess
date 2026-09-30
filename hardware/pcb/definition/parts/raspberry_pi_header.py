"""KiCad footprint and approved PCB binding for raspberry pi header."""

from pcb.definition.parts.land_patterns import pin_header
from pcb.definition.parts.part import PcbPart
from shared.components import PI_ZERO_HEADER
from shared.electronics.raspberry_pi_header import (
    RaspberryPiHeaderComponent as RaspberryPiHeader,
)
from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin

RASPBERRYPIHEADER_FOOTPRINT = pin_header(
    "2x20 2.54 mm THT",
    "Raspberry Pi Zero 2 W GPIO socket",
    columns=20,
    rows=2,
    pin_numbers=tuple(RaspberryPiHeaderPin),
)

RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM = 1.2

RASPBERRYPIHEADER_POWER_ESCAPE_MM = 6.0

RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_LENGTH_MM = 6.0

PI_ZERO_HEADER_PART = PcbPart(
    PI_ZERO_HEADER,
    RaspberryPiHeader,
    RASPBERRYPIHEADER_FOOTPRINT,
    "PI_HEADER",
    "2x20 header",
    "Raspberry Pi Zero 2 W GPIO socket",
)
