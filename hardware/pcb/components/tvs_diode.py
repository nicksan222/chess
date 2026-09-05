"""PCB specialization of the unidirectional input TVS diode D1."""

from domain.component import ComponentReference
from domain.footprint import Footprint, two_terminal_smd
from shared.electronics.passives import TvsDiodeComponent, TvsDiodePin


class TvsDiode(TvsDiodeComponent):
    POWER_ESCAPE_MM = 0.4
    POWER_ESCAPE_HORIZONTAL = False
    FOOTPRINT = two_terminal_smd(
        "SMB (DO-214AA)",
        "6 V unidirectional TVS diode",
        5.10,
        (2.20, 2.40),
        (4.6, 3.6),
        tuple(TvsDiodePin),
    )

    def footprint_for(self, package: str) -> Footprint:
        if package != self.FOOTPRINT.package:
            raise KeyError(f"{self.reference}: unsupported package {package!r}")
        return self.FOOTPRINT

    @staticmethod
    def signal_escape_distance_mm(pin_number: str) -> float:
        TvsDiodePin(pin_number)
        return 2.0


INPUT_TVS = TvsDiode(ComponentReference.INPUT_TVS)
TVS_SMB = TvsDiode.FOOTPRINT
