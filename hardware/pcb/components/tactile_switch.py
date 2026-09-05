"""PCB specialization of the four-leg tactile panel switch."""

from base import rules
from base.footprint import RECT, ROUND, Footprint, Pad, courtyard_for
from shared.electronics.tactile_switch import (
    TactileSwitchComponent,
    TactileSwitchPad,
    TactileSwitchPin,
)


class TactileSwitch(TactileSwitchComponent):
    """Own the paired-pad geometry and panel-label clearance."""

    _DRILL = rules.drill_for_lead(0.7)
    _PAD = rules.pad_for_drill(_DRILL)
    _PADS = (
        Pad(TactileSwitchPad.SIGNAL_PRIMARY, -3.25, 2.25, _PAD, _PAD, RECT, _DRILL),
        Pad(
            TactileSwitchPad.SIGNAL_DUPLICATE,
            -3.25,
            -2.25,
            _PAD,
            _PAD,
            ROUND,
            _DRILL,
        ),
        Pad(TactileSwitchPad.GROUND_PRIMARY, 3.25, 2.25, _PAD, _PAD, ROUND, _DRILL),
        Pad(
            TactileSwitchPad.GROUND_DUPLICATE,
            3.25,
            -2.25,
            _PAD,
            _PAD,
            ROUND,
            _DRILL,
        ),
    )
    FOOTPRINT = Footprint(
        "6x6 mm THT",
        "6 mm tactile panel switch, 9.5 mm actuator",
        _PADS,
        courtyard_for(_PADS, (6.2, 6.2)),
    )
    LABEL_OFFSET_MM = 6.5

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT


TACTILE_6MM = TactileSwitch.FOOTPRINT

__all__ = ("TactileSwitchPin",)
