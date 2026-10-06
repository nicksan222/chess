"""KiCad footprint and approved PCB binding for the E-Switch TL1105 panel button.

Role: the twelve front-panel buttons (SW1-SW12). The TL1105 has four through-hole
leads whose pairs 1-2 and 3-4 are internally strapped (E-Switch TL1105 p25), which
drives the pad mapping below: a wrong mapping would make every button read as
permanently pressed. Pin identities: `shared/electronics/tactile_switch.py`.
"""

import pcbnew

from pcb.definition import rules
from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import BUTTON
from shared.electronics.tactile_switch import TactileSwitchComponent as TactileSwitch
from shared.electronics.tactile_switch import TactileSwitchPad

# Drill from the lead diameter plus the board's through-hole clearance (`rules`).
TACTILESWITCH_DRILL = rules.drill_for_lead(0.7)

# Pad diameter giving the board's annular ring around that drill.
TACTILESWITCH_PAD = rules.pad_for_drill(TACTILESWITCH_DRILL)

# E-Switch TL1105 (2.28.2018) p25: datasheet pins 1-2 (6.50 apart) and 3-4 are
# internally connected; the dome bridges the pairs 4.50 apart. Drawn rotated -90 deg
# from the datasheet view: SIGNAL pads are datasheet 2 ("1") and 1 ("1b"), GROUND
# pads are 3 ("2") and 4 ("2b"). Holes Ø1.00.
# Pad "1"/"1b" are the same logical SIGNAL pin and "2"/"2b" the same GROUND pin;
# `native.logical_pin` maps the "b" pads back, so both pads of a pair get one net.
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
