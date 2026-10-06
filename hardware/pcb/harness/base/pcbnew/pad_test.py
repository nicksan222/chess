"""Contract tests for package-local copper pad declarations.

These tests exercise the model's shape, drill and numbering invariants. They
do not prove a manufacturer's land-pattern dimensions, solderability or a
finished board's connectivity.
"""

import unittest
from enum import StrEnum

from pcb.harness.base.pcbnew.pad import Pad, PadKind, PadShape
from pcb.harness.base.pcbnew.point import Point


class Pin(StrEnum):
    """Single logical contact used by these pad validation examples."""

    A = "1"


class PadTest(unittest.TestCase):
    def test_smd_pad_has_no_drill(self) -> None:
        """Surface pads default to SMD with the logical pin as pad number.

        The assertions prove the default kind and fallback number. They do not
        prove the dimensions match a real package or that the pad is connected
        to a board net.
        """
        pad = Pad(Pin.A, Point(-0.8, 0), 0.7, 0.8)
        # The default selects surface-mount copper and therefore no drill.
        self.assertEqual(pad.kind, PadKind.SURFACE)
        # The fallback number is a KiCad identity, not printed board text.
        self.assertEqual(pad.physical_number, "1")

    def test_drilled_pad_needs_a_hole_smaller_than_copper(self) -> None:
        """A hole larger than the pad would remove the copper ring, so it fails.

        The assertion proves this oversized drill is rejected. It does not prove
        a valid annulus meets a particular fabricator's minimum size.
        """
        with self.assertRaisesRegex(ValueError, "drill"):
            Pad(Pin.A, Point(0, 0), 1, 1, kind=PadKind.THROUGH_HOLE, drill_mm=1.2)

    def test_circle_requires_equal_dimensions(self) -> None:
        """A circle cannot be wider than it is tall or vice versa.

        The assertion proves unequal spans are rejected for the circle enum. It
        does not test oval geometry or the renderer's native shape mapping.
        """
        with self.assertRaisesRegex(ValueError, "circle"):
            Pad(Pin.A, Point(0, 0), 1, 2, shape=PadShape.CIRCLE)

    def test_duplicate_contact_can_have_distinct_physical_number(self) -> None:
        """One logical contact can own multiple distinctly numbered pads.

        The assertion proves an explicit number overrides the pin-label default.
        It does not prove that the two pads are electrically joined in KiCad;
        the component connection and generated net determine that later.
        """
        pad = Pad(Pin.A, Point(0, 0), 1, 1, number="1b")
        # The explicit label, not the logical pin's default "1", reaches KiCad.
        self.assertEqual(pad.physical_number, "1b")

    def test_bad_pad_number_type_is_rejected_cleanly(self) -> None:
        """Runtime callers cannot pass an integer as a KiCad pad identity."""
        with self.assertRaisesRegex(ValueError, "number"):
            Pad(Pin.A, Point(0, 0), 1, 1, number=3)  # type: ignore[arg-type]

    def test_non_numeric_copper_width_is_rejected_cleanly(self) -> None:
        """An invalid dynamic width produces a domain error, not TypeError."""
        with self.assertRaisesRegex(ValueError, "dimensions"):
            Pad(Pin.A, Point(0, 0), "wide", 1)  # type: ignore[arg-type]
