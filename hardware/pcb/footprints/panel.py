"""Parts a finger touches, plus the probes a meter touches."""

from __future__ import annotations

from components.barrel_jack import BarrelJackPad
from components.tactile_switch import TactileSwitchPad
from core import rules

from .base import RECT, ROUND, Footprint, Pad, courtyard_for

_TACT_DRILL = rules.drill_for_lead(0.7)
_TACT_PAD = rules.pad_for_drill(_TACT_DRILL)

# A 6 mm tactile switch has four legs in two shorted pairs, on a 6.5 by 4.5 mm
# rectangle. Both legs of a pair carry the same net, which is why the design contract
# models the part as two terminals while the footprint has four pads. The `b`
# suffix is what tells the netlist check they share a pin.
_TACT_PADS = (
    Pad(TactileSwitchPad.SIGNAL_PRIMARY, -3.25, 2.25, _TACT_PAD, _TACT_PAD, RECT, _TACT_DRILL),
    Pad(TactileSwitchPad.SIGNAL_DUPLICATE, -3.25, -2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
    Pad(TactileSwitchPad.GROUND_PRIMARY, 3.25, 2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
    Pad(TactileSwitchPad.GROUND_DUPLICATE, 3.25, -2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
)

TACTILE_6MM = Footprint(
    package="6x6 mm THT",
    description="6 mm tactile panel switch, 9.5 mm actuator",
    pads=_TACT_PADS,
    courtyard=courtyard_for(_TACT_PADS, (6.2, 6.2)),
)

# The PJ-102A has three terminals: the centre pin, the sleeve, and its normally
# closed switched sleeve contact. Both sleeve terminals are intentionally grounded.
_JACK_DRILL = rules.drill_for_lead(1.5)
_JACK_PAD = rules.pad_for_drill(_JACK_DRILL)
_JACK_PADS = (
    Pad(BarrelJackPad.CENTRE_POSITIVE, -4.5, 0.0, _JACK_PAD, _JACK_PAD, RECT, _JACK_DRILL),
    Pad(BarrelJackPad.SLEEVE_GROUND, 0.0, -4.85, _JACK_PAD, _JACK_PAD, ROUND, _JACK_DRILL),
    Pad(BarrelJackPad.SWITCHED_SLEEVE_GROUND, 4.5, 0.0, _JACK_PAD, _JACK_PAD, ROUND, _JACK_DRILL),
)

BARREL_JACK = Footprint(
    package="5.5x2.0 mm THT",
    description="Same Sky PJ-102A 5.5 x 2.0 mm DC jack, centre positive",
    pads=_JACK_PADS,
    courtyard=courtyard_for(_JACK_PADS, (13.0, 11.0)),
)
