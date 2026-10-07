"""Physical board features independent of component pin connections."""

from dataclasses import dataclass

from ..net import Net
from .point import Point
from .route import CopperLayer


@dataclass(frozen=True)
class MountingHole:
    reference: str
    center: Point
    diameter_mm: float


@dataclass(frozen=True)
class Label:
    text: str
    center: Point
    height_mm: float = 1.0
    width_mm: float = 0.2


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point
    width_mm: float = 0.2


@dataclass(frozen=True)
class Plane[BoardNet: Net]:
    net: BoardNet
    layer: CopperLayer
    inset_mm: float = 1.0
    clearance_mm: float = 0.5


@dataclass(frozen=True)
class BoardLayout[BoardNet: Net]:
    copper_layers: int = 2
    thickness_mm: float = 1.6
    minimum_clearance_mm: float | None = None
    minimum_track_width_mm: float | None = None
    edge_clearance_mm: float | None = None
    planes: tuple[Plane[BoardNet], ...] = ()
    holes: tuple[MountingHole, ...] = ()
    labels: tuple[Label, ...] = ()
    lines: tuple[Line, ...] = ()
