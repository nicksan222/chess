"""KiCad footprint and approved PCB binding for the TPS259474ARPW eFuse (U74).

TI SLVSFC9C p73, RPW0010A example board layout (measured from the vector drawing,
85 units/mm, checked against its 2.4/1.8/1.45/0.6/0.3/0.25 dimensions): IN (5) and
OUT (6) are 0.3 x 2.4 bars at x = -/+0.25; side pads 2, 3, 8, 9 are 0.6 x 0.25 at
(-/+0.9, +/-0.225); corner pads 1, 4, 7, 10 are L-shaped: a 0.6 x 0.3 foot at
(-/+0.9, +/-0.70) plus a 0.25-wide leg at x = -/+0.725 out to y = +/-1.2. Pin
roles: `shared/electronics/efuse.py`. Its 0.2 mm pad gaps need the scoped DRC rule
in `output/exports.py` (lead-approved S4b exception, U74 only).
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    courtyard_for,
    footprint,
    pad,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import EFUSE
from shared.electronics.efuse import EfuseComponent as Efuse
from shared.electronics.efuse import EfusePin

# Pad dimensions and offsets (mm) read from the TI drawing above, named so the pad table
# below reads as pins on a grid: `COLUMN_X` is the side-pad column, `SIDE_Y`/`FOOT_Y` the
# pad rows, and `BAR_X` the two long IN/OUT bars in the middle.
SIDE_PAD_MM = (0.6, 0.25)
BAR_PAD_MM = (0.3, 2.4)
FOOT_MM = (0.6, 0.3)
LEG_WIDTH_MM = 0.25
LEG_X_MM = 0.725
LEG_INNER_Y_MM = 0.85
LEG_OUTER_Y_MM = 1.2
COLUMN_X_MM = 0.9
FOOT_Y_MM = 0.70
SIDE_Y_MM = 0.225
BAR_X_MM = 0.25


def corner_pad(number: str, sx: int, sy: int) -> pcbnew.PAD:
    """Foot (anchor) plus the outward leg as a custom-pad primitive.

    `sx`/`sy` are the corner's signs (-1 or +1). The leg is part of the same pad, so the
    corner pin gets the L-shaped copper TI draws, with its leg running toward the package
    edge for routing.
    """
    result = pad(
        number, sx * COLUMN_X_MM, sy * FOOT_Y_MM, *FOOT_MM, pcbnew.PAD_SHAPE_RECT
    )
    result.SetShape(pcbnew.PAD_SHAPE_CUSTOM)
    result.SetAnchorPadShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECT)
    # Primitive coordinates are relative to the pad, in native Y-down units.
    dx = sx * (LEG_X_MM - COLUMN_X_MM)
    x0, x1 = dx - LEG_WIDTH_MM / 2, dx + LEG_WIDTH_MM / 2
    y0 = sy * (LEG_INNER_Y_MM - FOOT_Y_MM - FOOT_MM[1] / 2)
    y1 = sy * (LEG_OUTER_Y_MM - FOOT_Y_MM)
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    points = pcbnew.VECTOR_VECTOR2I()
    for x, y in corners:
        points.append(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(-y)))
    result.AddPrimitivePoly(pcbnew.F_Cu, points, 0, True)
    return result


# Pin order follows the package: 1-5 down the left column and bars, 6-10 back up the right
# (counter-clockwise from pin 1, the top-left corner pad).
EFUSE_PADS = (
    corner_pad(EfusePin.ENABLE_UVLO, -1, 1),
    pad(
        EfusePin.OVERVOLTAGE_LOCKOUT,
        -COLUMN_X_MM,
        SIDE_Y_MM,
        *SIDE_PAD_MM,
        pcbnew.PAD_SHAPE_RECT,
    ),
    pad(
        EfusePin.POWER_GOOD,
        -COLUMN_X_MM,
        -SIDE_Y_MM,
        *SIDE_PAD_MM,
        pcbnew.PAD_SHAPE_RECT,
    ),
    corner_pad(EfusePin.POWER_GOOD_THRESHOLD, -1, -1),
    pad(EfusePin.INPUT, -BAR_X_MM, 0.0, *BAR_PAD_MM, pcbnew.PAD_SHAPE_RECT),
    pad(EfusePin.OUTPUT, BAR_X_MM, 0.0, *BAR_PAD_MM, pcbnew.PAD_SHAPE_RECT),
    corner_pad(EfusePin.SLEW_RATE, 1, -1),
    pad(EfusePin.GROUND, COLUMN_X_MM, -SIDE_Y_MM, *SIDE_PAD_MM, pcbnew.PAD_SHAPE_RECT),
    pad(
        EfusePin.CURRENT_LIMIT,
        COLUMN_X_MM,
        SIDE_Y_MM,
        *SIDE_PAD_MM,
        pcbnew.PAD_SHAPE_RECT,
    ),
    corner_pad(EfusePin.OVERCURRENT_TIMER, 1, 1),
)

# TI's NSMD note allows "0.05 MAX" mask expansion; 0 keeps a 0.2 mm mask web
# between the 0.2 mm-gapped pads (PCBWay dam 0.1 mm).
for _pad in EFUSE_PADS:
    _pad.SetLocalSolderMaskMargin(0)

# The land (2.4 tall, 2.4 wide with legs) exceeds the 2.0 mm body.
EFUSE_FOOTPRINT = footprint(
    "VQFN-HR-10 RPW 2x2 mm",
    "TPS259474ARPW eFuse, TI RPW0010A",
    EFUSE_PADS,
    courtyard_for(EFUSE_PADS, (2.4, 2.4)),
)
add_polarity_marker(EFUSE_FOOTPRINT, EfusePin.ENABLE_UVLO)

EFUSE_PART = PcbPart(
    EFUSE,
    Efuse,
    EFUSE_FOOTPRINT,
    "EFUSE",
    "TPS259474ARPW",
    "Input eFuse: inrush, OVLO, reverse blocking, circuit breaker",
    DrawingView.MOUNTING_SIDE,
)
