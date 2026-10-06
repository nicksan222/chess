"""Human-scale placement and clearance facts, expressed in millimetres."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class Side(StrEnum):
    """The board face on which a component's body is mounted.

    A through-hole lead may reach both faces, but the body still has one side.
    The eventual board engine must decide how to flip the actual footprint.
    """

    TOP = "top"
    BOTTOM = "bottom"


@dataclass(frozen=True, slots=True)
class Placement:
    """A footprint centre, counterclockwise rotation and mounted side.

    X and Y are millimetres relative to the board design's chosen origin, with
    positive Y up in the drawing. Rotation is counterclockwise as viewed from
    the component's mounting side; a bottom-mounted part therefore mirrors in
    the board-top view. Coordinates are not KiCad page coordinates. Keeping
    that conversion out of definitions lets authors work in board dimensions;
    the native renderer performs the tool-specific conversion later.
    """

    x_mm: float
    y_mm: float
    rotation_degrees: float = 0.0
    side: Side = Side.TOP

    def __post_init__(self) -> None:
        """Reject coordinates that cannot describe a physical placement."""
        if not all(
            math.isfinite(value)
            for value in (self.x_mm, self.y_mm, self.rotation_degrees)
        ):
            raise ValueError("placement coordinates and rotation must be finite")
        if type(self.side) is not Side:
            raise ValueError("placement side must be a Side")


@dataclass(frozen=True, slots=True)
class Courtyard:
    """The rectangular keep-clear area around an unrotated component.

    Width and height include assembly clearance around pads and the body. The
    courtyard is neither copper nor an exact 3D model. A geometry engine will
    rotate it with the component and compare it with neighbouring areas. It is
    also the keep-clear rectangle used to ensure a placement remains inside a
    board outline; it does not itself detect overlap between components.
    """

    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Keep nonsensical clearance areas out of a component definition."""
        if any(
            not math.isfinite(value) or value <= 0
            for value in (self.width_mm, self.height_mm)
        ):
            raise ValueError("courtyard dimensions must be finite and positive")


def courtyards_overlap(
    first_placement: Placement,
    first: Courtyard,
    second_placement: Placement,
    second: Courtyard,
) -> bool:
    """Detect a real overlap between two rotated component keep-clear boxes.

    A courtyard is a rectangle centred on its placement and rotated with the
    part. For each of the two edge directions of both rectangles, project the
    boxes onto that direction. If any projection is separate or merely touches,
    the rectangles do not overlap. This separating-axis test avoids false
    collision reports from larger axis-aligned bounding boxes. Courtyards on
    opposite board faces reserve different assembly space, so they may share
    the same XY location. This does not check copper or through-hole clearance.
    """
    if first_placement.side is not second_placement.side:
        return False

    def axes(placement: Placement) -> tuple[tuple[float, float], ...]:
        angle = math.radians(placement.rotation_degrees)
        cosine, sine = math.cos(angle), math.sin(angle)
        return ((cosine, sine), (-sine, cosine))

    first_axes = axes(first_placement)
    second_axes = axes(second_placement)
    delta_x = second_placement.x_mm - first_placement.x_mm
    delta_y = second_placement.y_mm - first_placement.y_mm
    for axis_x, axis_y in (*first_axes, *second_axes):
        first_radius = first.width_mm / 2 * abs(
            axis_x * first_axes[0][0] + axis_y * first_axes[0][1]
        ) + first.height_mm / 2 * abs(
            axis_x * first_axes[1][0] + axis_y * first_axes[1][1]
        )
        second_radius = second.width_mm / 2 * abs(
            axis_x * second_axes[0][0] + axis_y * second_axes[0][1]
        ) + second.height_mm / 2 * abs(
            axis_x * second_axes[1][0] + axis_y * second_axes[1][1]
        )
        distance = abs(delta_x * axis_x + delta_y * axis_y)
        if distance >= first_radius + second_radius - 1e-9:
            return False
    return True
