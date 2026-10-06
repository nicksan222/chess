"""Check the single coordinate conversion used by every native renderer.

These are boundary tests: they inspect KiCad's integer coordinates after
``FromMM`` and verify the centred, Y-up harness convention becomes an
upper-left, Y-down page convention. They do not validate any board object.
"""

import importlib.util
import unittest

from pcb.harness.base.pcbnew.outline import BoardOutline
from pcb.harness.base.pcbnew.point import Point


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class NativePointTest(unittest.TestCase):
    """Check the coordinate convention at KiCad's integer-unit boundary."""

    def test_centre_and_top_left_use_one_consistent_origin(self) -> None:
        """The centre maps to page half-size and the top-left maps to zero."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.units import native_point

        outline = BoardOutline(20, 10)
        centre = native_point(Point(0, 0), outline)
        corner = native_point(Point(-10, 5), outline)
        # Board origin (0, 0) is half the 20 by 10 mm page from its upper-left.
        self.assertEqual((centre.x, centre.y), (pcbnew.FromMM(10), pcbnew.FromMM(5)))
        # The Y inversion and half-size shift place the design's top-left at page origin.
        self.assertEqual((corner.x, corner.y), (0, 0))
