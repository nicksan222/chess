"""Geometry used by the multilayer path search, in millimetres."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingSettings:
    track_width_mm: float = 0.31
    clearance_mm: float = 0.30
    via_diameter_mm: float = 0.9
    via_drill_mm: float = 0.4
    edge_clearance_mm: float = 0.5

    def __post_init__(self) -> None:
        if (
            any(
                not math.isfinite(value) or value <= 0
                for value in (
                    self.track_width_mm,
                    self.clearance_mm,
                    self.via_diameter_mm,
                    self.via_drill_mm,
                    self.edge_clearance_mm,
                )
            )
            or self.via_drill_mm >= self.via_diameter_mm
        ):
            raise ValueError(
                "routing dimensions must be positive with an annular via ring"
            )

    @property
    def track_keepout_mm(self) -> float:
        return self.clearance_mm + self.track_width_mm / 2 + 0.02

    @property
    def via_keepout_mm(self) -> float:
        return self.clearance_mm + self.via_diameter_mm / 2 + 0.02
