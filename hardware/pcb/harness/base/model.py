"""Package-local 3D geometry, shared by KiCad exports and imported assemblies.

Dimensions and centers are millimetres, with Z=0 on the mounting face and
positive Z away from the board. These are declared envelopes, not supplier CAD.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Solid3D:
    name: str
    size_mm: tuple[float, float, float]
    center_mm: tuple[float, float, float] = (0, 0, 0)
    color: tuple[float, float, float] = (0.10, 0.10, 0.11)
    shape: Literal["box", "cylinder"] = "box"

    def __post_init__(self) -> None:
        if (
            not self.name
            or any(
                not math.isfinite(v)
                for v in (*self.size_mm, *self.center_mm, *self.color)
            )
            or min(self.size_mm) <= 0
            or any(v < 0 or v > 1 for v in self.color)
            or self.shape not in ("box", "cylinder")
            or (self.shape == "cylinder" and self.size_mm[0] != self.size_mm[1])
        ):
            raise ValueError("3D solids need named, finite geometry and RGB colors")


@dataclass(frozen=True)
class Model3D:
    solids: tuple[Solid3D, ...]
    fidelity: str = "dimension-based envelope"

    def __post_init__(self) -> None:
        if not self.solids or len({s.name for s in self.solids}) != len(self.solids):
            raise ValueError("3D model needs distinct named solids")
        if not self.fidelity:
            raise ValueError("3D model must identify its fidelity")

    @classmethod
    def envelope(cls, size_mm: tuple[float, float, float]) -> Model3D:
        return cls((Solid3D("Body", size_mm, (0, 0, size_mm[2] / 2)),))


@dataclass(frozen=True)
class MatedZone:
    """Mated connector clearance slab along local -Y from its footprint origin."""

    start_mm: float
    end_mm: float
    width_mm: float
    height_mm: float
    role: Literal["housing", "wire_exit"] = "housing"

    def __post_init__(self) -> None:
        if (
            not all(
                math.isfinite(v)
                for v in (self.start_mm, self.end_mm, self.width_mm, self.height_mm)
            )
            or self.end_mm <= self.start_mm
            or min(self.width_mm, self.height_mm) <= 0
        ):
            raise ValueError("Mated zones require finite positive dimensions")
