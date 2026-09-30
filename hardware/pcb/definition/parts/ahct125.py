"""KiCad footprint and approved PCB binding for ahct125."""

from pcb.definition.parts.land_patterns import soic
from pcb.definition.parts.part import PcbPart
from shared.components import AHCT125
from shared.electronics.ahct125 import Ahct125Component as Ahct125
from shared.electronics.ahct125 import Ahct125Pin

AHCT125_FOOTPRINT = soic(
    "SOIC-14 1.27 mm",
    "SN74AHCT125DR narrow SOIC",
    14,
    5.4,
    (6.2, 8.7),
    tuple(Ahct125Pin),
)

AHCT125_PART = PcbPart(
    AHCT125,
    Ahct125,
    AHCT125_FOOTPRINT,
    "AHCT125",
    "SN74AHCT125DR",
    "Quad 5 V buffer accepts 3.3 V SPI clock and data",
)
