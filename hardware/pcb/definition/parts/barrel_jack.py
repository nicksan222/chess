"""KiCad footprint and approved PCB binding for barrel jack."""

import pcbnew

from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import PcbPart
from shared.components import BARREL_JACK
from shared.electronics import ComponentReference
from shared.electronics.barrel_jack import BarrelJackComponent as BarrelJack
from shared.electronics.barrel_jack import BarrelJackPad

BARRELJACK_SLOT_MM = (1.0, 1.6)

BARRELJACK_PAD_MM = (2.0, 2.6)

BARRELJACK_PADS = (
    pad(
        BarrelJackPad.CENTRE_POSITIVE,
        0.0,
        -3.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_RECT,
        *BARRELJACK_SLOT_MM,
    ),
    pad(
        BarrelJackPad.SLEEVE_GROUND,
        0.0,
        3.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_CIRCLE,
        *BARRELJACK_SLOT_MM,
    ),
    pad(
        BarrelJackPad.SWITCHED_SLEEVE_GROUND,
        -4.7,
        0.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_CIRCLE,
        *BARRELJACK_SLOT_MM,
    ),
)

BARRELJACK_FOOTPRINT = footprint(
    "5.5x2.0 mm THT",
    "Same Sky PJ-102A 5.5 x 2.0 mm DC jack, centre positive",
    BARRELJACK_PADS,
    courtyard_for(BARRELJACK_PADS, (14.4, 11.0)),
)

BARREL_JACK_PART = PcbPart(
    BARREL_JACK,
    BarrelJack,
    BARRELJACK_FOOTPRINT,
    "BARREL_JACK",
    "DC 5.5x2.0",
    "5 V DC input jack, centre positive",
)

DC_INPUT_JACK = BarrelJack(ComponentReference.DC_INPUT_JACK)
