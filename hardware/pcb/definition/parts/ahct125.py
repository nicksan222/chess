"""KiCad footprint and approved PCB binding for the SN74AHCT125DR (U5).

Role: the quad bus buffer that sits between the Pi's 3.3 V SPI clock/data and the
5 V SK9822 LED chain (level shifting). Used once, as U5 in `assemblies/controls.py`.
This file owns its native land pattern; pin identities live in
`shared/electronics/ahct125.py` and the approved product in `shared/components/`.
"""

from pcb.definition.parts.land_patterns import add_polarity_marker, soic
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import AHCT125
from shared.electronics.ahct125 import Ahct125Component as Ahct125
from shared.electronics.ahct125 import Ahct125Pin

# Narrow SOIC-14. Land geometry cross-checked by `tests/board/test_land_patterns.py`
# against TI SCLS264R p20-21 (D0014A): 5.4 mm pad-row spacing, 1.55 x 0.6 mm pads
# (the `soic()` default pad size, hence no override here).
AHCT125_FOOTPRINT = soic(
    "SOIC-14 1.27 mm",
    "SN74AHCT125DR narrow SOIC",
    14,
    5.4,
    (6.2, 8.7),
    tuple(Ahct125Pin),
)

# Silk dot at pin 1 so the IC is not assembled rotated.
add_polarity_marker(AHCT125_FOOTPRINT, "1")

# Binds product + pin model + footprint; the description appears in the BOM/schematic.
AHCT125_PART = PcbPart(
    AHCT125,
    Ahct125,
    AHCT125_FOOTPRINT,
    "AHCT125",
    "SN74AHCT125DR",
    "Quad 5 V buffer accepts 3.3 V SPI clock and data",
    DrawingView.MOUNTING_SIDE,
)
