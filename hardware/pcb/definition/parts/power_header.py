"""KiCad footprint and approved PCB binding for the J4 power-entry header.

Role: J4 (JST B4PS-VH, bottom side) is where the wired panel jack and rocker harness
plugs into the board (see `shared/electronics/harness.py`). It is a through-hole part on
the bottom, so it is placed with a true flip; its datasheet drawing is seen from the
mounting surface, which is why `DrawingView.MOUNTING_SIDE` matters here (S3c B1).
Pin identities: `shared/electronics/power_header.py`.
"""

import pcbnew

from pcb.definition import rules
from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    footprint,
    pad,
    widen_thermal_spokes,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import POWER_HEADER
from shared.electronics import ComponentReference
from shared.electronics.power_header import PowerHeaderComponent as PowerHeader
from shared.electronics.power_header import PowerHeaderPin

# JST VH catalogue p4, side-entry layout (viewed from the mounting side): four Ø1.65
# (+0.1) holes at 3.96, circuit 1 at the left; the plug enters from the -Y side, and
# the 15.78 x 10.9 body runs from about 1 mm behind the hole row toward the opening.
# Origin at the body centre: hole row at +4.45.
VH_HOLE_MM = 1.65
VH_PITCH_MM = 3.96
VH_HOLE_ROW_Y_MM = 10.9 / 2 - 1.0
VH_BODY_MM = (15.78, 10.9)
# Copper ring from the repository's annulus rule (the JST drawing gives holes only; this is
# an ASSUMPTION in `definition/verification.py`).
VH_PAD_MM = rules.pad_for_drill(VH_HOLE_MM)

# Circuit 1 at index 0 (square pad), circuits counted left to right as JST draws them.
POWERHEADER_PADS = tuple(
    pad(
        pin,
        (index - 1.5) * VH_PITCH_MM,
        VH_HOLE_ROW_Y_MM,
        VH_PAD_MM,
        VH_PAD_MM,
        pcbnew.PAD_SHAPE_RECT if index == 0 else pcbnew.PAD_SHAPE_CIRCLE,
        VH_HOLE_MM,
    )
    for index, pin in enumerate(PowerHeaderPin)
)

POWERHEADER_FOOTPRINT = footprint(
    "VH 4P side entry THT",
    "JST B4PS-VH power-entry header, side entry",
    POWERHEADER_PADS,
    (VH_BODY_MM[0] + 0.5, VH_BODY_MM[1] + 0.5),
)

add_polarity_marker(POWERHEADER_FOOTPRINT, "1")
# This header carries the supply into the planes through its pads; give them wide
# thermal spokes so plane entry meets the ampacity tests.
widen_thermal_spokes(POWERHEADER_FOOTPRINT)

POWER_HEADER_PART = PcbPart(
    POWER_HEADER,
    PowerHeader,
    POWERHEADER_FOOTPRINT,
    "POWER_HEADER",
    "VH 4P",
    "Power entry: jack and rocker harness",
    DrawingView.MOUNTING_SIDE,
)

# Typed handle for J4 so routing and tests can address it by role, not by reference text.
POWER_ENTRY_HEADER = PowerHeader(ComponentReference.POWER_ENTRY_HEADER)
