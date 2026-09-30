"""KiCad footprint and approved PCB binding for sk9822."""

import pcbnew

from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import PcbPart
from shared.components import SK9822
from shared.electronics.sk9822 import Sk9822Component as Sk9822
from shared.electronics.sk9822 import Sk9822Pin

SK9822_BODY_MM = (5.0, 5.0)

SK9822_PAD_LONG_MM = 1.5

SK9822_PAD_SHORT_MM = 1.0

SK9822_PAD_EDGE_MM = 2.5

SK9822_SIGNAL_PITCH_MM = 1.6

SK9822_PADS = (
    pad(
        Sk9822Pin.DATA_IN,
        -SK9822_PAD_EDGE_MM,
        SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_RECT,
    ),
    pad(
        Sk9822Pin.CLOCK_IN,
        -SK9822_PAD_EDGE_MM,
        -SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.DATA_OUT,
        SK9822_PAD_EDGE_MM,
        SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.CLOCK_OUT,
        SK9822_PAD_EDGE_MM,
        -SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.FIVE_VOLTS,
        0.0,
        SK9822_PAD_EDGE_MM,
        SK9822_PAD_SHORT_MM,
        SK9822_PAD_LONG_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.GROUND,
        0.0,
        -SK9822_PAD_EDGE_MM,
        SK9822_PAD_SHORT_MM,
        SK9822_PAD_LONG_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
)

SK9822_FOOTPRINT = footprint(
    "PLCC-6 5050",
    "SK9822 clocked addressable RGB LED",
    SK9822_PADS,
    courtyard_for(SK9822_PADS, SK9822_BODY_MM),
)

SK9822_PART = PcbPart(
    SK9822,
    Sk9822,
    SK9822_FOOTPRINT,
    "SK9822",
    "SK9822",
    SK9822.description,
)
