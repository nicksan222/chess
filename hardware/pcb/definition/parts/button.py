"""KiCad footprint and approved PCB binding for button."""

import pcbnew

from pcb.definition import rules
from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import PcbPart
from shared.components import BUTTON
from shared.electronics.tactile_switch import TactileSwitchComponent as TactileSwitch
from shared.electronics.tactile_switch import TactileSwitchPad

TACTILESWITCH_DRILL = rules.drill_for_lead(0.7)

TACTILESWITCH_PAD = rules.pad_for_drill(TACTILESWITCH_DRILL)

TACTILESWITCH_PADS = (
    pad(
        TactileSwitchPad.SIGNAL_PRIMARY,
        -3.25,
        2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_RECT,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.SIGNAL_DUPLICATE,
        -3.25,
        -2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.GROUND_PRIMARY,
        3.25,
        2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.GROUND_DUPLICATE,
        3.25,
        -2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
)

TACTILESWITCH_FOOTPRINT = footprint(
    "6x6 mm THT",
    "6 mm tactile panel switch, 9.5 mm actuator",
    TACTILESWITCH_PADS,
    courtyard_for(TACTILESWITCH_PADS, (6.2, 6.2)),
)

TACTILESWITCH_LABEL_OFFSET_MM = 6.5

BUTTON_PART = PcbPart(
    BUTTON,
    TactileSwitch,
    TACTILESWITCH_FOOTPRINT,
    "BUTTON",
    "TACT 6mm",
    "Momentary panel button, 9.5 mm actuator",
)
