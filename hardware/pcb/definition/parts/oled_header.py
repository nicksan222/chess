"""KiCad footprint and approved PCB binding for the OLED harness header (J2).

Role: J2 (JST SM04B-SRSS-TB, SMD side entry) takes the four-wire harness to the OLED
module that sits in the tile plate. The plug enters from the tab side, which is why the
placement opens toward the module (`shared/dimensions/panel.py`). Pin identities:
`shared/electronics/connectors.py`.
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    courtyard_for,
    footprint,
    pad,
)
from pcb.definition.parts.part import DrawingView, PcbPart
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
