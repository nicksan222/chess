"""KiCad footprint and approved PCB binding for oled header."""

from pcb.definition.parts.land_patterns import pin_header
from pcb.definition.parts.part import PcbPart
from shared.components import OLED_HEADER
from shared.electronics.connectors import OledHeaderComponent as OledHeader
from shared.electronics.connectors import OledHeaderPin

OLEDHEADER_FOOTPRINT = pin_header(
    "1x4 2.54 mm THT",
    "Four-pin SSD1306 I2C OLED module connector",
    columns=4,
    rows=1,
    pin_numbers=tuple(OledHeaderPin),
)

OLED_HEADER_PART = PcbPart(
    OLED_HEADER,
    OledHeader,
    OLEDHEADER_FOOTPRINT,
    "OLED_HEADER",
    "1x4 header",
    "SSD1306 OLED module connector",
)
