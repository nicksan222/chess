"""KiCad footprint and approved PCB binding for test point."""

import pcbnew

from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import PcbPart
from shared.components import TEST_POINT
from shared.electronics.test_point import TestPointComponent as TestPoint
from shared.electronics.test_point import TestPointPin

TESTPOINT_PADS = (pad(TestPointPin.PROBE, 0.0, 0.0, 2.5, 1.25, pcbnew.PAD_SHAPE_RECT),)

TESTPOINT_FOOTPRINT = footprint(
    "SMD test point",
    "Low-profile SMT probe loop",
    TESTPOINT_PADS,
    courtyard_for(TESTPOINT_PADS, (2.0, 1.2)),
)

TEST_POINT_PART = PcbPart(
    TEST_POINT,
    TestPoint,
    TESTPOINT_FOOTPRINT,
    "TESTPOINT",
    "TEST",
    TEST_POINT.description,
)
