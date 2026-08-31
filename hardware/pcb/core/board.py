"""Board envelope in shared mechanical coordinates."""

from core import sources


class Board:
    def __init__(self) -> None:
        shared = sources.dimensions()
        self.width, self.height, _ = shared.PCB_SIZE_MM
        self.x_min = -self.width / 2.0
        self.x_max = self.width / 2.0
        self.y_max = shared.PLAYING_SPAN_MM / 2.0
        self.y_min = self.y_max - self.height

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (
            self.x_min + margin <= x <= self.x_max - margin
            and self.y_min + margin <= y <= self.y_max - margin
        )
