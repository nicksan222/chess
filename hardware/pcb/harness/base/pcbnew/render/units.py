"""Convert the harness drawing convention into KiCad's integer page space.

The harness deliberately describes a board with its origin at the centre,
millimetres as units, and positive Y upwards. ``pcbnew`` stores integer
internal units with positive Y downwards from the page's upper-left. Keeping
that translation in one function means every native shape uses the same
origin, axis direction, and KiCad unit conversion.
"""

from __future__ import annotations

import pcbnew

from ..outline import BoardOutline
from ..point import Point


def native_point(point: Point, outline: BoardOutline) -> pcbnew.VECTOR2I:
    """Place a centred drawing point in KiCad's upper-left page coordinates.

    Harness coordinates use the board centre as (0, 0), with positive Y toward
    the top. KiCad uses integer internal units with positive Y downward. Adding
    half the board dimensions shifts the origin to its upper-left corner, and
    subtracting Y flips the vertical direction. ``FromMM`` performs the unit
    conversion; no separate rounding policy is exposed by the harness. This
    function changes coordinates only; it does not create a native board item.
    """
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(outline.width_mm / 2 + point.x_mm),
        pcbnew.FromMM(outline.height_mm / 2 - point.y_mm),
    )
