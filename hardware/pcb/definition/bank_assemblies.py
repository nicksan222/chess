"""PCB identities and placements for the eight logical Hall banks."""

from dataclasses import dataclass

from shared import dimensions
from shared.hall_banks import HallBank

Point = tuple[float, float]
TCA9554_BYPASS_OFFSET_MM: Point = (8.0, 6.0)


@dataclass(frozen=True, slots=True)
class HallBankAssembly:
    """One Hall bank's stable PCB references and physical placement."""

    bank: HallBank
    expander_reference: str
    bypass_reference: str
    expander_position_mm: Point

    @property
    def label(self) -> str:
        return self.bank.label

    @property
    def assembly_name(self) -> str:
        return f"sensing/{self.label}"

    @property
    def address(self) -> int:
        return self.bank.address

    @property
    def bypass_position_mm(self) -> Point:
        x, y = self.expander_position_mm
        offset_x, offset_y = TCA9554_BYPASS_OFFSET_MM
        return (x + offset_x, y + offset_y)


def _assembly(label: str, expander: str, bypass: str) -> HallBankAssembly:
    bank = next(bank for bank in dimensions.HALL_BANKS if bank.label == label)
    x, y = dimensions.EXPANDER_POSITIONS_BY_BANK_MM[label]
    return HallBankAssembly(
        bank,
        expander,
        bypass,
        (x, y),
    )


# Published references are explicit identities, never allocated by traversal.
BANK_ASSEMBLIES = (
    _assembly("A1-D2", "U1", "C3"),
    _assembly("E1-H2", "U2", "C4"),
    _assembly("A3-D4", "U3", "C5"),
    _assembly("E3-H4", "U4", "C6"),
    _assembly("A5-D6", "U70", "C136"),
    _assembly("E5-H6", "U71", "C137"),
    _assembly("A7-D8", "U72", "C138"),
    _assembly("E7-H8", "U73", "C139"),
)
