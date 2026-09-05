"""PCB specialization of the centre-positive Same Sky PJ-102A jack."""

from domain.component import ComponentReference
from domain.footprint import RECT, ROUND, Footprint, Pad, courtyard_for
from shared.electronics.barrel_jack import (
    BarrelJackComponent,
    BarrelJackPad,
    BarrelJackPin,
)


class BarrelJack(BarrelJackComponent):
    """Own the manufacturer's plated slots, pad spacing, and body envelope."""

    SLOT_MM = (1.0, 1.6)
    PAD_MM = (2.0, 2.6)
    _PADS = (
        Pad(BarrelJackPad.CENTRE_POSITIVE, 0.0, -3.0, *PAD_MM, RECT, *SLOT_MM),
        Pad(BarrelJackPad.SLEEVE_GROUND, 0.0, 3.0, *PAD_MM, ROUND, *SLOT_MM),
        Pad(
            BarrelJackPad.SWITCHED_SLEEVE_GROUND,
            -4.7,
            0.0,
            *PAD_MM,
            ROUND,
            *SLOT_MM,
        ),
    )
    FOOTPRINT = Footprint(
        "5.5x2.0 mm THT",
        "Same Sky PJ-102A 5.5 x 2.0 mm DC jack, centre positive",
        _PADS,
        courtyard_for(_PADS, (14.4, 11.0)),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT


DC_INPUT_JACK = BarrelJack(ComponentReference.DC_INPUT_JACK)
BARREL_JACK = BarrelJack.FOOTPRINT

__all__ = ("BarrelJackPin",)
