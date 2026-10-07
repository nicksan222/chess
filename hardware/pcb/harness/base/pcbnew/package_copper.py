"""Copper geometry in package coordinates, independent of any board instance."""

import math
from dataclasses import dataclass
from enum import StrEnum

from .point import Point


@dataclass(frozen=True)
class PackagePath:
    pin: StrEnum
    points: tuple[Point, ...]
    width_mm: float
    via: bool = False

    def __post_init__(self) -> None:
        if (
            len(self.points) < 2
            or not math.isfinite(self.width_mm)
            or self.width_mm <= 0
        ):
            raise ValueError("package path needs points and a positive width")


@dataclass(frozen=True)
class PackageVia:
    pin: StrEnum
    center: Point


@dataclass(frozen=True)
class PackageClearance:
    clearance_mm: float
    track_width_mm: float
    escape_margin_mm: float

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value) or value <= 0
            for value in (self.clearance_mm, self.track_width_mm, self.escape_margin_mm)
        ):
            raise ValueError("package clearance dimensions must be finite and positive")
