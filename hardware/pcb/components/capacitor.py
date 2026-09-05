"""PCB specializations of the approved board capacitors."""

from typing import ClassVar

from base.footprint import Footprint, two_pad_axial, two_terminal_smd
from shared.electronics.passives import CapacitorComponent, CapacitorPin


class Capacitor(CapacitorComponent):
    """Select the land pattern belonging to the capacitor's approved package."""

    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    CAPACITOR_0603 = two_terminal_smd(
        "0603 (1608 metric)",
        "100 nF X7R MLCC",
        1.50,
        (0.90, 0.95),
        (1.6, 0.8),
        tuple(CapacitorPin),
    )
    CAPACITOR_0805 = two_terminal_smd(
        "0805 (2012 metric)",
        "10 uF X5R MLCC",
        1.90,
        (1.00, 1.40),
        (2.0, 1.25),
        tuple(CapacitorPin),
    )
    ELECTROLYTIC_10MM = two_pad_axial(
        "radial 10 mm",
        "1000 uF radial electrolytic",
        pitch=5.0,
        lead_diameter=0.8,
        body=(10.5, 10.5),
        pin_numbers=tuple(CapacitorPin),
    )
    LED_BYPASS_OFFSET_MM = (0.0, -8.0)
    HALL_BYPASS_OFFSET_MM = (0.0, -3.0)
    FOOTPRINTS: ClassVar[dict[str, Footprint]] = {
        footprint.package: footprint
        for footprint in (CAPACITOR_0603, CAPACITOR_0805, ELECTROLYTIC_10MM)
    }

    def footprint_for(self, package: str) -> Footprint:
        try:
            return self.FOOTPRINTS[package]
        except KeyError as error:
            raise KeyError(
                f"{self.reference}: unsupported package {package!r}"
            ) from error

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        CapacitorPin(pin_number)
        return 2.0


CAPACITOR_0603 = Capacitor.CAPACITOR_0603
CAPACITOR_0805 = Capacitor.CAPACITOR_0805
ELECTROLYTIC_10MM = Capacitor.ELECTROLYTIC_10MM
