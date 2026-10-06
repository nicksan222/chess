"""Board locations in millimetres, before conversion to KiCad page space.

The harness uses the board centre as its origin and follows the usual drawing
convention of positive Y pointing toward the top of the board. Keeping that
small coordinate system here means component and routing declarations do not
need to know about KiCad's integer units or upper-left page origin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import cast


@dataclass(frozen=True, slots=True)
class Point:
    """An immutable board coordinate, expressed in millimetres.

    For a pad, the point is relative to its component centre. For a component,
    trace, via or outline operation, it is relative to the board centre. Keeping
    the same value type for both makes the origin context important: the field
    documentation on each operation states which origin applies. The rendering
    adapter converts points into KiCad's integer coordinates, where Y increases
    downward from the page's upper-left corner. Negative coordinates are valid;
    the board outline, rather than ``Point``, decides whether a location fits.
    """

    x_mm: float
    y_mm: float

    def __post_init__(self) -> None:
        """Reject NaN and infinity before geometry or unit conversion uses them.

        This keeps comparisons, trigonometry and KiCad's integer conversion
        deterministic. It does not check board containment because a point may
        be package-local or may be intentionally outside an outline while a
        larger object is being assembled.
        """
        if any(
            not isinstance(value, Real)
            or isinstance(cast(object, value), bool)
            or not math.isfinite(value)
            for value in (self.x_mm, self.y_mm)
        ):
            raise ValueError("board point coordinates must be finite")
