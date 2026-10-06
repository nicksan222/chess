"""KiCad footprint and approved PCB binding for the SK9822 5050 RGB LED.

Role: one clocked, daisy-chained RGB LED per square (64 in a serpentine chain, see
`shared/squares.py`). The 5050 package has three leads per side. An earlier footprint
did not match either SK9822 package; this one is drawn
from the Opsco SPC/SK9822-A Rev 01 recommended land. Pin identities and chain
direction: `shared/electronics/sk9822.py`.
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    courtyard_for,
    footprint,
    pad,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import SK9822
from shared.electronics.sk9822 import Sk9822Component as Sk9822
from shared.electronics.sk9822 import Sk9822Pin

# Body outline used only for the courtyard.
SK9822_BODY_MM = (5.0, 5.0)

# Opsco SPC/SK9822-A Rev 01 p4 §6 recommended PCB land (top view): 1.80 mm wide
# pads, 0.40 mm apart along a 4.40 mm column (so 1.20 mm high at 1.60 mm pitch),
# 3.40 mm inner gap. Pins 1-3 run up the right side from the chamfered corner,
# pins 4-6 down the left (p3 §4: three 1.0 mm leads per side within 4.2 mm).
SK9822_PAD_SIZE_MM = (1.8, 1.2)

SK9822_COLUMN_MM = 3.4 / 2.0 + SK9822_PAD_SIZE_MM[0] / 2.0

SK9822_PITCH_MM = 1.6

# Pad centres in the datasheet top view (Y up). Inputs (pins 1-2) are on +X, outputs
# (5-6) on -X; assemblies/square.py rotates each LED so outputs face the next LED.
SK9822_PAD_CENTRES_MM = {
    Sk9822Pin.DATA_IN: (SK9822_COLUMN_MM, -SK9822_PITCH_MM),
    Sk9822Pin.CLOCK_IN: (SK9822_COLUMN_MM, 0.0),
    Sk9822Pin.GROUND: (SK9822_COLUMN_MM, SK9822_PITCH_MM),
    Sk9822Pin.FIVE_VOLTS: (-SK9822_COLUMN_MM, SK9822_PITCH_MM),
    Sk9822Pin.CLOCK_OUT: (-SK9822_COLUMN_MM, 0.0),
    Sk9822Pin.DATA_OUT: (-SK9822_COLUMN_MM, -SK9822_PITCH_MM),
}

# Pin 1 (data in) is RECT as the polarity cue; the others are oval.
SK9822_PADS = tuple(
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
