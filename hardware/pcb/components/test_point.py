"""PCB specialization of the low-profile probe point."""

from base.footprint import RECT, Footprint, Pad, courtyard_for
from shared.electronics.test_point import TestPointComponent, TestPointPin


class TestPoint(TestPointComponent):
    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    _PADS = (Pad(TestPointPin.PROBE, 0.0, 0.0, 2.5, 1.25, RECT),)
    FOOTPRINT = Footprint(
        "SMD test point",
        "Low-profile SMT probe loop",
        _PADS,
        courtyard_for(_PADS, (2.0, 1.2)),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        TestPointPin(pin_number)
        return 2.0


TEST_POINT_SMD = TestPoint.FOOTPRINT
