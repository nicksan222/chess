"""Typed declarations for solderable copper lands in a component package.

Pads are package-local geometry, not board coordinates: their centre is an
offset from the component centre, and all dimensions are millimetres. The
renderer adds the component placement and converts the result to KiCad's
native units.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from numbers import Real
from typing import cast

from .point import Point


class PadKind(StrEnum):
    """Choose surface-mount copper or a plated through-hole land.

    Surface-mount parts solder onto copper on one board face. Through-hole
    parts have leads through drilled holes and copper lands around the holes.
    This choice determines the KiCad pad attribute and copper-layer set; it
    does not describe whether the component body is on the top or bottom side.
    """

    SURFACE = "surface"
    THROUGH_HOLE = "through_hole"


class PadShape(StrEnum):
    """Select the copper land outline supported by the board renderer.

    ``OVAL`` means a rounded-ended elongated land. The enum is deliberately
    small so every declared shape has a known KiCad mapping.
    """

    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    OVAL = "oval"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class Pad[Pin: StrEnum]:
    """Describe one solderable copper land in package-local coordinates.

    ``pin`` identifies the logical electrical contact; a four-leg button can
    have two physical pads connected to the same contact. ``number`` is the
    KiCad pad identity used to distinguish those pieces of copper; it is not a
    silkscreen label. ``center`` is measured from the component centre, and
    width, height and drill are in millimetres. Through-hole drill size must
    leave copper around the hole. The renderer turns these choices into KiCad
    pad shape, layers, size, drill, number and (when connected) net. Valid
    values do not prove they match the component's manufacturer drawing.
    """

    pin: Pin
    center: Point
    width_mm: float
    height_mm: float
    kind: PadKind = PadKind.SURFACE
    shape: PadShape = PadShape.RECTANGLE
    drill_mm: float = 0.0
    number: str | None = None
    # Optional rectangle-anchored polygon, in pad-local millimetres/Y-up.
    polygon: tuple[Point, ...] = ()
    solder_mask_margin_mm: float | None = None
    thermal_spoke_width_mm: float | None = None
    solid_zone_connection: bool = False

    def __post_init__(self) -> None:
        """Reject values that could produce ambiguous or unmanufacturable pads.

        Typed pins and enums keep the renderer from receiving unrelated
        component data. Positive finite copper dimensions give a real land;
        finite nonnegative drills support SMD's zero drill and PTH's positive
        drill. A through-hole drill must be smaller than both copper spans so
        an annulus remains. Circle pads need equal spans, and safe physical
        numbers keep generated KiCad identifiers predictable.
        """
        if not isinstance(cast(object, self.pin), StrEnum):
            raise ValueError("pad pin must be a typed pin enum")
        if not isinstance(cast(object, self.center), Point):
            raise ValueError("pad center must be a Point")
        if any(
            not isinstance(value, Real)
            or isinstance(cast(object, value), bool)
            or not math.isfinite(value)
            or value <= 0
            for value in (self.width_mm, self.height_mm)
        ):
            raise ValueError("pad copper dimensions must be finite and positive")
        if (
            not isinstance(self.drill_mm, Real)
            or isinstance(cast(object, self.drill_mm), bool)
            or not math.isfinite(self.drill_mm)
            or self.drill_mm < 0
        ):
            raise ValueError("pad drill must be finite and nonnegative")
        if not isinstance(cast(object, self.kind), PadKind) or not isinstance(
            cast(object, self.shape), PadShape
        ):
            raise ValueError("pad kind and shape must use their enums")
        if self.kind is PadKind.SURFACE and self.drill_mm != 0:
            raise ValueError("surface pad cannot have a drill")
        if self.kind is PadKind.THROUGH_HOLE and not 0 < self.drill_mm < min(
            self.width_mm, self.height_mm
        ):
            raise ValueError("through-hole pad drill must fit inside copper")
        if self.shape is PadShape.CIRCLE and self.width_mm != self.height_mm:
            raise ValueError("circle pad needs equal width and height")
        if self.shape is PadShape.CUSTOM:
            if self.kind is not PadKind.SURFACE or len(self.polygon) < 3:
                raise ValueError("custom surface pad needs a polygon")
            if any(
                not isinstance(cast(object, point), Point) for point in self.polygon
            ):
                raise ValueError("custom pad vertices must be Points")
            if len(set(self.polygon)) != len(self.polygon):
                raise ValueError("custom pad polygon needs distinct vertices")
            area = sum(
                a.x_mm * b.y_mm - b.x_mm * a.y_mm
                for a, b in zip(self.polygon, self.polygon[1:] + self.polygon[:1])
            )
            if abs(area) < 1e-12:
                raise ValueError("custom pad polygon needs nonzero area")
        elif self.polygon:
            raise ValueError("polygon requires a custom pad")
        for value in (self.solder_mask_margin_mm, self.thermal_spoke_width_mm):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(
                    "pad mask and thermal settings must be finite and nonnegative"
                )
        if self.thermal_spoke_width_mm == 0:
            raise ValueError("thermal spoke width must be positive")
        if not isinstance(cast(object, self.physical_number), str) or not re.fullmatch(
            r"[A-Za-z0-9_]+", self.physical_number
        ):
            raise ValueError("pad needs a safe physical number")

    @property
    def physical_number(self) -> str:
        """Return the KiCad pad number, defaulting to the logical pin label."""
        return self.number if self.number is not None else str(self.pin)
