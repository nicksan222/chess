"""PCB specialization of the active-low TI DRV5032 Hall sensor."""

from domain.footprint import OBLONG, RECT, Footprint, Pad, courtyard_for
from shared.electronics.hall_sensor import HallSensorComponent, HallSensorPin


class HallSensor(HallSensorComponent):
    """Own the SOT-23 land pattern and breakout length used under each square."""

    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    _PADS = (
        Pad(HallSensorPin.SUPPLY, -0.95, 0.95, 1.00, 1.10, RECT),
        Pad(HallSensorPin.ACTIVE_LOW_OUTPUT, -0.95, -0.95, 1.00, 1.10, OBLONG),
        Pad(HallSensorPin.GROUND, 0.95, 0.0, 1.00, 1.10, OBLONG),
    )
    FOOTPRINT = Footprint(
        "SOT-23-3",
        "DRV5032FC omnipolar Hall sensor",
        _PADS,
        courtyard_for(_PADS, (2.9, 2.8)),
    )
    SIGNAL_ESCAPE_MM = 3.0

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @classmethod
    def signal_escape_distance_mm(cls, pin_number: str) -> float:
        cls.pin_type(pin_number)
        return cls.SIGNAL_ESCAPE_MM


HALL_SOT23 = HallSensor.FOOTPRINT
