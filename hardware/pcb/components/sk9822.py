"""PCB specialization of the six-pad SK9822 5050 LED."""

from domain.footprint import OBLONG, RECT, Footprint, Pad, courtyard_for
from shared.electronics.sk9822 import Sk9822Component, Sk9822Pin


class Sk9822(Sk9822Component):
    """Own package dimensions and the signal-chain escape clearances."""

    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    BODY_MM = (5.0, 5.0)
    PAD_LONG_MM = 1.5
    PAD_SHORT_MM = 1.0
    PAD_EDGE_MM = 2.5
    SIGNAL_PITCH_MM = 1.6
    _PADS = (
        Pad(
            Sk9822Pin.DATA_IN,
            -PAD_EDGE_MM,
            SIGNAL_PITCH_MM / 2.0,
            PAD_LONG_MM,
            PAD_SHORT_MM,
            RECT,
        ),
        Pad(
            Sk9822Pin.CLOCK_IN,
            -PAD_EDGE_MM,
            -SIGNAL_PITCH_MM / 2.0,
            PAD_LONG_MM,
            PAD_SHORT_MM,
            OBLONG,
        ),
        Pad(
            Sk9822Pin.DATA_OUT,
            PAD_EDGE_MM,
            SIGNAL_PITCH_MM / 2.0,
            PAD_LONG_MM,
            PAD_SHORT_MM,
            OBLONG,
        ),
        Pad(
            Sk9822Pin.CLOCK_OUT,
            PAD_EDGE_MM,
            -SIGNAL_PITCH_MM / 2.0,
            PAD_LONG_MM,
            PAD_SHORT_MM,
            OBLONG,
        ),
        Pad(
            Sk9822Pin.FIVE_VOLTS,
            0.0,
            PAD_EDGE_MM,
            PAD_SHORT_MM,
            PAD_LONG_MM,
            OBLONG,
        ),
        Pad(
            Sk9822Pin.GROUND,
            0.0,
            -PAD_EDGE_MM,
            PAD_SHORT_MM,
            PAD_LONG_MM,
            OBLONG,
        ),
    )
    FOOTPRINT = Footprint(
        "PLCC-6 5050",
        "SK9822 clocked addressable RGB LED",
        _PADS,
        courtyard_for(_PADS, BODY_MM),
    )
    DEFAULT_SIGNAL_ESCAPE_MM = 2.0

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @classmethod
    def signal_escape_distance_mm(cls, pin_number: str) -> float:
        cls.pin_type(pin_number)
        return cls.DEFAULT_SIGNAL_ESCAPE_MM


SK9822_5050 = Sk9822.FOOTPRINT
