"""PCB specialization of the surface-mount input fuse F1."""

from domain.component import ComponentReference
from domain.footprint import Footprint, two_terminal_smd
from shared.electronics.passives import FuseComponent, FusePin


class Fuse(FuseComponent):
    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    FOOTPRINT = two_terminal_smd(
        "2410 fuse",
        "5 A time-delay surface-mount fuse",
        6.60,
        (2.70, 3.20),
        (6.1, 2.7),
        tuple(FusePin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        FusePin(pin_number)
        return 2.0


INPUT_FUSE = Fuse(ComponentReference.INPUT_FUSE)
FUSE_2410 = Fuse.FOOTPRINT
