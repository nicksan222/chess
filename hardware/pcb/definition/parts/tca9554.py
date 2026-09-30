"""KiCad footprint and approved PCB binding for tca9554."""

from pcb.definition.parts.land_patterns import soic
from pcb.definition.parts.part import PcbPart
from shared.components import TCA9554
from shared.electronics.tca9554 import Tca9554Component as Tca9554
from shared.electronics.tca9554 import Tca9554Pin

TCA9554_FOOTPRINT = soic(
    "SOIC-16W 1.27 mm",
    "TCA9554DWR wide SOIC, TI DW0016A",
    16,
    9.3,
    (7.6, 10.5),
    tuple(Tca9554Pin),
    pad_size_mm=(2.0, 0.6),
)


TCA9554_SILKSCREEN_CLEARANCE_MM = 2.0

TCA9554_PART = PcbPart(
    TCA9554,
    Tca9554,
    TCA9554_FOOTPRINT,
    "TCA9554",
    "TCA9554DWR",
    "8-bit I2C GPIO expander with input pull-ups",
)
