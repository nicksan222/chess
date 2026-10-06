"""Contract tests for explicit traces and drilled vias.

The checks cover declaration-level geometry and typed-net retention. They do
not prove a complete route, clearance, native KiCad output or manufactured
signal integrity.
"""

import unittest

from pcb.harness import Net
from pcb.harness.base.pcbnew.point import Point
from pcb.harness.base.pcbnew.route import CopperLayer, Trace, Via


class Nets(Net):
    """Typed design net used to check route declarations."""

    POWER = "+3V3"


class RouteTest(unittest.TestCase):
    def test_trace_needs_two_distinct_points(self) -> None:
        """A zero-length segment is not a useful copper connection.

        The assertion proves coincident endpoints are rejected. It does not
        prove that two distinct endpoints touch pads or form a connected route.
        """
        with self.assertRaisesRegex(ValueError, "distinct"):
            Trace(Nets.POWER, Point(0, 0), Point(0, 0), CopperLayer.TOP, 0.2)

    def test_via_drill_must_fit_inside_copper(self) -> None:
        """A drill wider than the via's copper diameter is rejected.

        The assertion proves the minimum annulus invariant for this oversized
        drill. It does not prove compliance with a manufacturer's annulus rule.
        """
        with self.assertRaisesRegex(ValueError, "drill"):
            Via(Nets.POWER, Point(0, 0), diameter_mm=0.5, drill_mm=0.6)

    def test_valid_trace_keeps_typed_net(self) -> None:
        """The declaration retains the same enum member rather than a raw label.

        The assertion proves logical net identity survives construction. It does
        not prove native connectivity, endpoint contact or a valid route path.
        """
        route = Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.TOP, 0.2)
        # This checks the route's logical identity; it does not prove board
        # connectivity.
        self.assertIs(route.net, Nets.POWER)

    def test_trace_rejects_non_point_endpoint(self) -> None:
        """Invalid dynamic endpoint input gets a clear model error."""
        with self.assertRaisesRegex(ValueError, "Point"):
            Trace(Nets.POWER, (0, 0), Point(1, 0), CopperLayer.TOP, 0.2)  # type: ignore[arg-type]

    def test_via_rejects_non_point_center(self) -> None:
        """A via requires a validated board-coordinate Point."""
        with self.assertRaisesRegex(ValueError, "Point"):
            Via(Nets.POWER, (0, 0), 0.7, 0.3)  # type: ignore[arg-type]

    def test_trace_rejects_non_numeric_width_cleanly(self) -> None:
        """A malformed track width never reaches the KiCad unit converter."""
        with self.assertRaisesRegex(ValueError, "width"):
            Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.TOP, "wide")  # type: ignore[arg-type]

    def test_via_rejects_non_numeric_drill_cleanly(self) -> None:
        """A malformed drilled hole produces a domain error."""
        with self.assertRaisesRegex(ValueError, "drill"):
            Via(Nets.POWER, Point(0, 0), 0.7, "large")  # type: ignore[arg-type]
