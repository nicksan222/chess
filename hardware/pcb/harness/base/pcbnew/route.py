"""Tool-independent declarations for copper traces, layers and vias.

Routes use the board-centred millimetre coordinate system from :mod:`point`.
They intentionally describe author intent before KiCad conversion, so routing
code can validate typed nets and dimensions without constructing native SDK
objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from numbers import Real
from typing import cast

from ..net import Net
from .point import Point


class CopperLayer(StrEnum):
    """The top and bottom outer copper faces available to route declarations."""

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True, slots=True)
class Trace[BoardNet: Net]:
    """One straight copper segment for an electrical net on one board face.

    The start and end are board-centred coordinates in millimetres. The layer
    selects the top or bottom outer copper face, and ``width_mm`` is the copper
    track width. This describes exactly one straight segment; it does not route
    around obstacles or create connections at either end. A native board
    renderer can draw it, while connectivity and clearance checks must inspect
    the result.
    """

    net: BoardNet
    start: Point
    end: Point
    layer: CopperLayer
    width_mm: float

    def __post_init__(self) -> None:
        """Reject a segment that cannot represent usable typed copper.

        The net/layer checks reject values outside those two categories;
        ``Circuit.trace`` later checks the net belongs to this board's enum.
        Distinct endpoints give the segment nonzero length, and a
        finite positive width gives KiCad a real track. These checks do not
        establish pad contact, collision-free routing or electrical continuity.
        """
        if not isinstance(cast(object, self.net), Net) or not isinstance(
            cast(object, self.layer), CopperLayer
        ):
            raise ValueError("trace needs typed net and copper layer")
        if not isinstance(cast(object, self.start), Point) or not isinstance(
            cast(object, self.end), Point
        ):
            raise ValueError("trace endpoints must be Point values")
        if self.start == self.end:
            raise ValueError("trace endpoints must be distinct")
        if (
            not isinstance(self.width_mm, Real)
            or isinstance(cast(object, self.width_mm), bool)
            or not math.isfinite(self.width_mm)
            or self.width_mm <= 0
        ):
            raise ValueError("trace width must be finite and positive")


@dataclass(frozen=True, slots=True)
class Via[BoardNet: Net]:
    """One plated hole joining the board's top and bottom copper faces.

    ``diameter_mm`` is the outside copper diameter; ``drill_mm`` is the hole
    diameter. Both are millimetres, and the difference leaves a copper ring
    around the drilled hole. The declaration currently models a through-via;
    it does not choose a via technology or prove manufacturing rules.
    """

    net: BoardNet
    center: Point
    diameter_mm: float
    drill_mm: float

    def __post_init__(self) -> None:
        """Require a positive drill smaller than the finite copper diameter.

        This preserves an annulus of copper around the hole and prevents
        non-finite dimensions from reaching KiCad. It does not check annulus
        width against a fabricator rule or prove that the via connects two
        other copper objects.
        """
        if not isinstance(cast(object, self.net), Net):
            raise ValueError("via needs a typed net")
        if not isinstance(cast(object, self.center), Point):
            raise ValueError("via center must be a Point")
        if (
            not isinstance(self.diameter_mm, Real)
            or isinstance(cast(object, self.diameter_mm), bool)
            or not isinstance(self.drill_mm, Real)
            or isinstance(cast(object, self.drill_mm), bool)
            or not math.isfinite(self.diameter_mm)
            or not math.isfinite(self.drill_mm)
            or not 0 < self.drill_mm < self.diameter_mm
        ):
            raise ValueError("via drill must be positive and smaller than copper")
