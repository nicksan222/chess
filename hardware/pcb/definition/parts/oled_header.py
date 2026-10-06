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

# JST SH catalogue p1, side-entry land (viewed from the mounting side): signal pads
# 0.6 x 1.55 at 1.0 pitch, pin 1 left; reinforcement pads 1.2 x 1.8 with their inner
# edge 0.7 beyond the last signal centre; signal-pad row 5.55 - 4 = 1.55 tall from
# y 4.0, tab row 1.8 tall from y 0. The plug enters from the tab side. Origin midway
# between the rows (2.8375 above the tab row bottom).
SH_SIGNAL_PAD_MM = (0.6, 1.55)
SH_TAB_PAD_MM = (1.2, 1.8)
SH_ROW_OFFSET_MM = 4.775 - 2.8375
SH_TAB_X_MM = 1.5 + 0.7 + 0.6

OLEDHEADER_PADS = (
    *(
        pad(
            pin,
            -1.5 + index,
            SH_ROW_OFFSET_MM,
            *SH_SIGNAL_PAD_MM,
            pcbnew.PAD_SHAPE_RECT if index == 0 else pcbnew.PAD_SHAPE_OVAL,
        )
        for index, pin in enumerate(
            (
                OledHeaderPin.GROUND,
                OledHeaderPin.THREE_VOLTS_THREE,
                OledHeaderPin.I2C_CLOCK,
                OledHeaderPin.I2C_DATA,
            )
        )
    ),
    pad(
        OledHeaderPin.MOUNTING_TAB_A,
        -SH_TAB_X_MM,
        -SH_ROW_OFFSET_MM,
        *SH_TAB_PAD_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        OledHeaderPin.MOUNTING_TAB_B,
        SH_TAB_X_MM,
        -SH_ROW_OFFSET_MM,
        *SH_TAB_PAD_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
)

OLEDHEADER_FOOTPRINT = footprint(
    "SH 4P side entry SMD",
    "JST SM04B-SRSS-TB OLED harness header, side entry",
    OLEDHEADER_PADS,
    courtyard_for(OLEDHEADER_PADS, (6.0, 4.95)),
)

add_polarity_marker(OLEDHEADER_FOOTPRINT, "1")

OLED_HEADER_PART = PcbPart(
    OLED_HEADER,
    OledHeader,
    OLEDHEADER_FOOTPRINT,
    "OLED_HEADER",
    "SH 4P",
    "OLED harness header (module wired by its pad labels)",
    DrawingView.MOUNTING_SIDE,
)
