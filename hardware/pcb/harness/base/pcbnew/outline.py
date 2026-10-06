"""The rectangular physical board edge and outline containment checks.

This module describes the board boundary in the same centre-origin millimetres
used by the authoring contracts. The renderer later turns it into KiCad
``Edge.Cuts`` graphics; the dataclass itself is tool-independent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import cast

from ..geometry import Courtyard, Placement


@dataclass(frozen=True, slots=True)
class BoardOutline:
    """A positive rectangular PCB centred on the design origin.

    ``width_mm`` and ``height_mm`` are full spans in millimetres, so the board
    extends to half each dimension on either side of (0, 0). The edge bounds
    where the manufactured board ends. The renderer draws it on KiCad's
    edge-cuts layer. This initial shape cannot express tabs or cut-outs; such
    geometry needs a later outline kind with its own explicit validation.
    """

    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Require finite, positive spans so the boundary is meaningful.

        Zero or negative dimensions would make containment and page conversion
        ambiguous; non-finite values would poison those calculations.
        """
        if any(
            not isinstance(value, Real)
            or isinstance(cast(object, value), bool)
            or not math.isfinite(value)
            or value <= 0
            for value in (self.width_mm, self.height_mm)
        ):
            raise ValueError("board outline dimensions must be finite and positive")

    def contains(self, placement: Placement, courtyard: Courtyard) -> bool:
        """Check that a rotated keep-clear box fits within the board boundary.

        The placement is board-centred and the courtyard is the reserved
        rectangle around a part used to leave room for assembly. Rotation is in
        degrees counterclockwise. The rotated rectangle's axis-aligned extents
        are compared with the outline's half-width and half-height. This catches
        a part too close to the board edge; it does not detect overlap with
        another part or prove room for soldering and tools.
        """
        angle = math.radians(placement.rotation_degrees)
        cosine, sine = abs(math.cos(angle)), abs(math.sin(angle))
        half_x = (courtyard.width_mm * cosine + courtyard.height_mm * sine) / 2
        half_y = (courtyard.width_mm * sine + courtyard.height_mm * cosine) / 2
        return (
            abs(placement.x_mm) + half_x <= self.width_mm / 2
            and abs(placement.y_mm) + half_y <= self.height_mm / 2
        )
