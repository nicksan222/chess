"""Reusable rectangular board-envelope geometry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BoardEnvelope:
    width: float
    height: float
    y_max: float

    @property
    def x_min(self) -> float:
        return -self.width / 2.0

    @property
    def x_max(self) -> float:
        return self.width / 2.0

    @property
    def y_min(self) -> float:
        return self.y_max - self.height

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (
            self.x_min + margin <= x <= self.x_max - margin
            and self.y_min + margin <= y <= self.y_max - margin
        )
