"""Package-local pad exits, shared by every instance of a component."""

import math
from dataclasses import dataclass
from enum import StrEnum

from .package_copper import PackageClearance, PackagePath, PackageVia
from .point import Point


class EscapeAxis(StrEnum):
    AUTO = "auto"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class PackageRouting:
    paths: tuple[PackagePath, ...] = ()
    vias: tuple[PackageVia, ...] = ()
    ports: tuple[tuple[str, Point], ...] = ()
    clearance: PackageClearance | None = None
    signal_mm: float = 2.0
    signal_axis: EscapeAxis = EscapeAxis.AUTO
    signal_by_pin: tuple[tuple[str, float], ...] = ()
    power_mm: float = 0.4
    power_axis: EscapeAxis = EscapeAxis.AUTO
    power_by_pin: tuple[tuple[str, float], ...] = ()
    power_width_mm: float = 0.31
    power_via_count: int = 1
    power_via_pitch_mm: float = 1.2

    def __post_init__(self) -> None:
        if len({name for name, _ in self.ports}) != len(self.ports):
            raise ValueError("package port names must be unique")
        values = (
            self.signal_mm,
            self.power_mm,
            *(value for _, value in self.signal_by_pin),
            *(value for _, value in self.power_by_pin),
        )
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("package escapes must be finite and nonnegative")
        if any(
            len({pin for pin, _ in entries}) != len(entries)
            for entries in (self.signal_by_pin, self.power_by_pin)
        ):
            raise ValueError("package escape pin overrides must be unique")
        if self.power_via_count < 1 or self.power_via_count % 2 != 1:
            raise ValueError("power fanout requires a positive odd via count")
        if any(
            not math.isfinite(value) or value <= 0
            for value in (self.power_width_mm, self.power_via_pitch_mm)
        ):
            raise ValueError("fanout width and pitch must be finite and positive")

    def signal_distance(self, pin: str) -> float:
        return dict(self.signal_by_pin).get(pin, self.signal_mm)

    def power_distance(self, pin: str) -> float:
        return dict(self.power_by_pin).get(pin, self.power_mm)
