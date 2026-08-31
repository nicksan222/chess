"""Parts a finger touches, plus the probes a meter touches."""

from __future__ import annotations

from core import rules

from .base import RECT, ROUND, Footprint, Pad, courtyard_for

_TACT_DRILL = rules.drill_for_lead(0.7)
_TACT_PAD = rules.pad_for_drill(_TACT_DRILL)

# A 6 mm tactile switch has four legs in two shorted pairs, on a 6.5 by 4.5 mm
# rectangle. Both legs of a pair carry the same net, which is why the design contract
# models the part as two terminals while the footprint has four pads. The `b`
# suffix is what tells the netlist check they share a pin.
_TACT_PADS = (
    Pad("1", -3.25, 2.25, _TACT_PAD, _TACT_PAD, RECT, _TACT_DRILL),
    Pad("1b", -3.25, -2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
    Pad("2", 3.25, 2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
    Pad("2b", 3.25, -2.25, _TACT_PAD, _TACT_PAD, ROUND, _TACT_DRILL),
)

TACTILE_6MM = Footprint(
    package="6x6 mm THT",
    description="6 mm tactile panel switch, 9.5 mm actuator",
    pads=_TACT_PADS,
    courtyard=courtyard_for(_TACT_PADS, (6.2, 6.2)),
)

_TURRET_DRILL = rules.drill_for_lead(1.0)
_TURRET_PAD = rules.pad_for_drill(_TURRET_DRILL)
_TURRET_PADS = (
    Pad("1", 0.0, 0.0, _TURRET_PAD, _TURRET_PAD, ROUND, _TURRET_DRILL),
)

TESTPOINT_TURRET = Footprint(
    package="turret 1.6 mm THT",
    description="Turret test point",
    pads=_TURRET_PADS,
    courtyard=courtyard_for(_TURRET_PADS),
)

# A DC-005 style jack has three terminals: the centre pin, the sleeve, and a
# switched sleeve contact that is unused here. The design contract models two nets, so
# the third pad carries the sleeve net rather than being left floating.
_JACK_DRILL = rules.drill_for_lead(1.5)
_JACK_PAD = rules.pad_for_drill(_JACK_DRILL)
_JACK_PADS = (
    Pad("1", -4.5, 0.0, _JACK_PAD, _JACK_PAD, RECT, _JACK_DRILL),
    Pad("2", 0.0, -4.85, _JACK_PAD, _JACK_PAD, ROUND, _JACK_DRILL),
    Pad("2b", 4.5, 0.0, _JACK_PAD, _JACK_PAD, ROUND, _JACK_DRILL),
)

BARREL_JACK = Footprint(
    package="5.5x2.1 mm THT",
    description="5.5 x 2.1 mm DC jack, centre positive",
    pads=_JACK_PADS,
    courtyard=courtyard_for(_JACK_PADS, (13.0, 11.0)),
)
