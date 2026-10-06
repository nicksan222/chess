"""KiCad footprint and approved PCB binding for the Raspberry Pi header socket (J1).

Role: the 2x20 socket on the board's bottom side that the Pi's male header plugs into.
Its holes must sit exactly under the Pi's pins (`tests/board/test_pi_header.py`), which
is why the drawing is viewed from the board top (`DrawingView.BOARD_TOP`) and the part is
placed on the bottom side, without mirroring its pads, by the shared Pi transform. Pin identities:
`shared/electronics/raspberry_pi_header.py`.
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    SULLINS_HOLE_MM,
    add_polarity_marker,
    pin_header,
)
from pcb.definition.parts.part import DrawingView, PcbPart
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
    # Sullins .100" female header catalogue p81: recommended Ø1.02 holes.
    drill=SULLINS_HOLE_MM,
    pin_numbers=tuple(RaspberryPiHeaderPin),
)

add_polarity_marker(RASPBERRYPIHEADER_FOOTPRINT, "1")

# Routing keep-out geometry for the button escapes and the 5 V pin power escape; used by
# `routing/policies.py` (mm).
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
    DrawingView.BOARD_TOP,
)

# Mid-row pins at 2.54 pitch leave room for only one thermal spoke between the
# neighbouring pads' clearances (KiCad "starved thermal"); the Pi's 3.3 V pins
# therefore join the +3V3 plane solidly.
for _pad in RASPBERRYPIHEADER_FOOTPRINT.Pads():
    if _pad.GetNumber() in (
        RaspberryPiHeaderPin.THREE_VOLTS_THREE,
        RaspberryPiHeaderPin.THREE_VOLTS_THREE_ALT,
    ):
        _pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
