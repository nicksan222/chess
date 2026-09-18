"""Physical placement of one-off components on the PCB control strip."""

from dataclasses import dataclass
from types import MappingProxyType

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoardPlacement:
    centre_mm: Point
    rotation_degrees: float = 0.0

    @property
    def x_mm(self) -> float:
        return self.centre_mm[0]

    @property
    def y_mm(self) -> float:
        return self.centre_mm[1]


PCB_STRIP_PLACEMENTS = MappingProxyType(
    {
        "J3": BoardPlacement((-150.0, -178.0), -90.0),
        "F1": BoardPlacement((-138.0, -178.0)),
        "D1": BoardPlacement((-150.0, -165.0)),
        "SW13": BoardPlacement((-113.0, -190.0)),
        "C1": BoardPlacement((-128.0, -170.0)),
        "C2": BoardPlacement((-116.0, -168.0)),
        "J2": BoardPlacement((-95.0, -172.0)),
        "U5": BoardPlacement((-70.0, -180.0)),
        "C7": BoardPlacement((-58.0, -180.0)),
        "R1": BoardPlacement((-50.0, -170.0)),
        "R2": BoardPlacement((-50.0, -176.0)),
        "TP1": BoardPlacement((-47.0, -165.0)),
        "TP2": BoardPlacement((-40.0, -165.0)),
        "TP3": BoardPlacement((-33.0, -165.0)),
        "TP4": BoardPlacement((-26.0, -165.0)),
        "TP5": BoardPlacement((-19.0, -165.0)),
        "TP6": BoardPlacement((-12.0, -165.0)),
        "TP7": BoardPlacement((-47.0, -196.0)),
    }
)
