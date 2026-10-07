"""Plain data describing how an existing electrical net should become copper."""

import math
from dataclasses import dataclass
from enum import StrEnum

from ...connections import Endpoint
from ...net import Net
from ..point import Point
from ..route import CopperLayer, Via


@dataclass(frozen=True)
class PinLaunch:
    """A connector's reserved exit corridor and permitted fallback copper layers."""

    reference: str
    fallback_layers: tuple[CopperLayer, ...]
    x_offset_mm: float = 0.0
    length_mm: float = 4.5
    keepout_half_width_mm: float = 1.2
    keepout_length_mm: float = 6.0


@dataclass(frozen=True)
class NetRoute:
    net: Net
    layers: tuple[CopperLayer, ...] = (CopperLayer.TOP, CopperLayer.BOTTOM)
    width_mm: float = 0.31
    preferred_layer: CopperLayer | None = None
    area: tuple[float, float, float, float] | None = None
    diagonals: bool = False
    allow_vias: bool = True
    prune_unused_vias: bool = False
    priority: int = 0
    launch: PinLaunch | None = None
    reserve_group: bool = False
    omit: tuple[Endpoint, ...] = ()
    escapes: tuple[tuple[Endpoint, Point], ...] = ()
    last_reference: str | None = None
    via_keepout_mm: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.via_keepout_mm) or self.via_keepout_mm < 0:
            raise ValueError("via keepout must be finite and nonnegative")
        overrides = tuple(endpoint for endpoint, _ in self.escapes)
        if len(set(overrides)) != len(overrides) or set(overrides) & set(self.omit):
            raise ValueError("route escapes must be unique and cannot be omitted")
        if not self.layers or len(set(self.layers)) != len(self.layers):
            raise ValueError("net route needs distinct copper layers")
        if self.preferred_layer is not None and self.preferred_layer not in self.layers:
            raise ValueError("preferred layer must be enabled for this route")
        if not math.isfinite(self.width_mm) or self.width_mm <= 0:
            raise ValueError("net route width must be finite and positive")
        if self.area is not None:
            left, bottom, right, top = self.area
            if (
                not all(math.isfinite(value) for value in self.area)
                or left >= right
                or bottom >= top
            ):
                raise ValueError("routing area must be a finite, ordered rectangle")


def validate_routes(circuit_net_type: type[Net], routes: tuple[NetRoute, ...]) -> None:
    if any(type(route.net) is not circuit_net_type for route in routes):
        raise ValueError("route must use the circuit's net enum")
    if len({route.net for route in routes}) != len(routes):
        raise ValueError("each net needs one routing declaration")


class Bend(StrEnum):
    HORIZONTAL_FIRST = "horizontal_first"
    VERTICAL_FIRST = "vertical_first"


@dataclass(frozen=True)
class CopperPath:
    """An intentional path through named pins and board-centred waypoints."""

    net: Net
    points: tuple[Endpoint | Point, ...]
    layer: CopperLayer = CopperLayer.TOP
    width_mm: float = 0.31
    bend: Bend | None = None

    def __post_init__(self) -> None:
        if (
            len(self.points) < 2
            or not math.isfinite(self.width_mm)
            or self.width_mm <= 0
        ):
            raise ValueError("copper path needs endpoints and a positive width")
        if self.bend is not None and len(self.points) != 2:
            raise ValueError("a chosen bend joins exactly two endpoints")


@dataclass(frozen=True)
class DirectLink:
    """Join two pins directly when clear; otherwise defer obstacle-aware routing."""

    net: Net
    start: Endpoint
    end: Endpoint


@dataclass(frozen=True)
class RouteStage:
    paths: tuple[CopperPath, ...] = ()
    vias: tuple[Via[Net], ...] = ()
    links: tuple[DirectLink, ...] = ()
    nets: tuple[NetRoute, ...] = ()


@dataclass(frozen=True)
class RoutingPlan:
    root_reference: str
    power_nets: tuple[Net, ...]
    power_exclusions: tuple[str, ...]
    stages: tuple[RouteStage, ...]
