"""KiCad footprint and approved PCB binding for the Harwin S1751-46R test point.

Role: probe points on selected nets (e.g. buffered LED data/clock, I2C) so the board
can be measured during bring-up. Single-pad, SMD.
"""

import pcbnew

from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import TEST_POINT
from shared.electronics.test_point import TestPointComponent as TestPoint
from shared.electronics.test_point import TestPointPin

# Harwin SMT Hardware p260: S1751-46R recommended PC board pattern 3.45 x 1.85.
TESTPOINT_PADS = (pad(TestPointPin.PROBE, 0.0, 0.0, 3.45, 1.85, pcbnew.PAD_SHAPE_RECT),)

TESTPOINT_FOOTPRINT = footprint(
    "SMD test point",
    "Low-profile SMT probe loop",
    TESTPOINT_PADS,
    courtyard_for(TESTPOINT_PADS, (3.25, 1.65)),
)

TEST_POINT_PART = PcbPart(
    TEST_POINT,
    TestPoint,
    TESTPOINT_FOOTPRINT,
    "TESTPOINT",
    "TEST",
    TEST_POINT.description,
    DrawingView.MOUNTING_SIDE,
)
