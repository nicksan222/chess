"""KiCad footprint and approved PCB binding for the TCA9554DWR Hall-bank expander.

Role: the 8-bit I2C GPIO expander placed once per Hall bank (U1-U4, U70-U73, see
`bank_assemblies.py`); its eight inputs read the bank's Hall sensors. Chosen part
property used by the design: input pull-ups (the DRV5032 Hall output is open-drain, so
it relies on the expander's integrated 100 kohm pull-up while the port is an input;
TI SCPS233E section 8.3). Pin identities: `shared/electronics/tca9554.py`.
"""

from pcb.definition.parts.land_patterns import add_polarity_marker, soic
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import TCA9554
from shared.electronics.tca9554 import Tca9554Component as Tca9554
from shared.electronics.tca9554 import Tca9554Pin

# Wide SOIC-16 (TI DW0016A). Pad geometry is overridden from the `soic()` default and
# checked in `tests/board/test_land_patterns.py` against TI SCPS233E p39-40: 9.3 mm
# pad-row spacing, 2.0 x 0.6 mm pads, 1.27 mm pitch.
TCA9554_FOOTPRINT = soic(
    "SOIC-16W 1.27 mm",
    "TCA9554DWR wide SOIC, TI DW0016A",
    16,
    9.3,
    (7.6, 10.5),
    tuple(Tca9554Pin),
    pad_size_mm=(2.0, 0.6),
)

add_polarity_marker(TCA9554_FOOTPRINT, "1")


# Offset of the bank label (e.g. "U1 I2C 0x20 A1-D2") beyond the courtyard's top edge;
# consumed by `output/markings.py`. Not a keep-out applied to other silkscreen.
TCA9554_SILKSCREEN_CLEARANCE_MM = 2.0

TCA9554_PART = PcbPart(
    TCA9554,
    Tca9554,
    TCA9554_FOOTPRINT,
    "TCA9554",
    "TCA9554DWR",
    "8-bit I2C GPIO expander with input pull-ups",
    DrawingView.MOUNTING_SIDE,
)
