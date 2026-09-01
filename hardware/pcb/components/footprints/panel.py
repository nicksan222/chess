"""Parts a finger touches, plus the probes a meter touches."""

from __future__ import annotations

from base import rules
from base.footprint import RECT, ROUND, Footprint, Pad, courtyard_for
from components.barrel_jack import BarrelJackPad
from components.tactile_switch import TactileSwitchPad

_TACT_DRILL = rules.drill_for_lead(0.7)
_TACT_PAD = rules.pad_for_drill(_TACT_DRILL)

# A 6 mm tactile switch has four legs in two shorted pairs, on a 6.5 by 4.5 mm
# rectangle. Both legs of a pair carry the same net, which is why the design contract
# models the part as two terminals while the footprint has four pads. The `b`
# suffix is what tells the netlist check they share a pin.
_TACT_PADS = (
    Pad(
        TactileSwitchPad.SIGNAL_PRIMARY,
        -3.25,
        2.25,
        _TACT_PAD,
        _TACT_PAD,
        RECT,
        _TACT_DRILL,
    ),
    Pad(
        TactileSwitchPad.SIGNAL_DUPLICATE,
        -3.25,
        -2.25,
        _TACT_PAD,
        _TACT_PAD,
        ROUND,
        _TACT_DRILL,
    ),
    Pad(
        TactileSwitchPad.GROUND_PRIMARY,
        3.25,
        2.25,
        _TACT_PAD,
        _TACT_PAD,
        ROUND,
        _TACT_DRILL,
    ),
    Pad(
        TactileSwitchPad.GROUND_DUPLICATE,
        3.25,
        -2.25,
        _TACT_PAD,
        _TACT_PAD,
        ROUND,
        _TACT_DRILL,
    ),
)

TACTILE_6MM = Footprint(
    package="6x6 mm THT",
    description="6 mm tactile panel switch, 9.5 mm actuator",
    pads=_TACT_PADS,
    courtyard=courtyard_for(_TACT_PADS, (6.2, 6.2)),
)

# Same Sky drawing PJ-102A, rev. 2024-02-15: three tapered 1.0 x 1.6 mm
# terminals. Pin 1 and pin 2 are 6.0 mm apart; pin 3 is offset 4.7 mm from
# their centreline. The plated slots, rather than oversized round holes, retain
# the jack against insertion force. Both sleeve terminals are grounded.
_JACK_SLOT_MM = (1.0, 1.6)
_JACK_PAD_MM = (2.0, 2.6)
_JACK_PADS = (
    Pad(
        BarrelJackPad.CENTRE_POSITIVE,
        0.0,
        -3.0,
        *_JACK_PAD_MM,
        RECT,
        *_JACK_SLOT_MM,
    ),
    Pad(
        BarrelJackPad.SLEEVE_GROUND,
        0.0,
        3.0,
        *_JACK_PAD_MM,
        ROUND,
        *_JACK_SLOT_MM,
    ),
    Pad(
        BarrelJackPad.SWITCHED_SLEEVE_GROUND,
        -4.7,
        0.0,
        *_JACK_PAD_MM,
        ROUND,
        *_JACK_SLOT_MM,
    ),
)

BARREL_JACK = Footprint(
    package="5.5x2.0 mm THT",
    description="Same Sky PJ-102A 5.5 x 2.0 mm DC jack, centre positive",
    pads=_JACK_PADS,
    courtyard=courtyard_for(_JACK_PADS, (14.4, 11.0)),
)
