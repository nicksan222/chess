"""Contract tests for the harness coordinate type.

These tests establish finite millimetre values and their sign/identity
semantics. They do not exercise the KiCad coordinate conversion; that belongs
to the renderer's unit tests.
"""

import unittest

from pcb.harness.base.pcbnew.point import Point


class PointTest(unittest.TestCase):
    def test_accepts_finite_center_relative_millimetres(self) -> None:
        """Finite package-local coordinates may be negative or positive.

        The assertion proves that the value is retained as millimetres. It does
        not prove that the point is inside a board or that KiCad can render it.
        """
        # The x coordinate is retained as millimetres; no KiCad conversion occurs here.
        self.assertEqual(Point(-1.5, 2).x_mm, -1.5)

    def test_rejects_nonfinite_coordinate(self) -> None:
        """NaN cannot identify a stable physical location.

        The assertion proves that a NaN x coordinate is rejected with the
        public validation error. It does not separately test infinity or NaN in
        the y coordinate.
        """
        with self.assertRaisesRegex(ValueError, "finite"):
            Point(float("nan"), 0)

    def test_rejects_non_numeric_coordinate_cleanly(self) -> None:
        """A dynamic caller gets a domain error before KiCad sees a bad point."""
        with self.assertRaisesRegex(ValueError, "finite"):
            Point("left", 0)  # type: ignore[arg-type]

    def test_rejects_boolean_coordinate(self) -> None:
        """A truth value is not a millimetre measurement."""
        with self.assertRaisesRegex(ValueError, "finite"):
            Point(True, 0)
