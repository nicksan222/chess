"""PCB specialization of the approved pull-up resistor."""

from base.footprint import Footprint, two_terminal_smd
from shared.electronics.passives import ResistorComponent, ResistorPin


class Resistor(ResistorComponent):
    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    FOOTPRINT = two_terminal_smd(
        "0603 (1608 metric)",
        "100 nF X7R MLCC",
        1.50,
        (0.90, 0.95),
        (1.6, 0.8),
        tuple(ResistorPin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        ResistorPin(pin_number)
        return 2.0
