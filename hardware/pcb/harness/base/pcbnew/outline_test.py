"""Contract tests for a centred rectangular board edge.

The assertions cover dimension validation and rotated courtyard containment;
they do not inspect native ``Edge.Cuts`` graphics or manufacturing DRC.
"""

import unittest

from pcb.harness import Courtyard, Placement
from pcb.harness.base.pcbnew.outline import BoardOutline


class BoardOutlineTest(unittest.TestCase):
    def test_non_numeric_dimension_is_rejected_cleanly(self) -> None:
        """An invalid dimension cannot leak into rotated containment math."""
        with self.assertRaisesRegex(ValueError, "dimensions"):
            BoardOutline("wide", 10)  # type: ignore[arg-type]

    def test_rejects_zero_width(self) -> None:
        """An edge with zero width cannot describe a physical rectangle.

        The assertion proves the public error is raised for this invalid input.
        It does not cover negative or non-finite dimensions.
        """
        with self.assertRaisesRegex(ValueError, "positive"):
            BoardOutline(0, 20)

    def test_rotated_courtyard_must_stay_inside_board(self) -> None:
        """Containment accounts for rotation and rejects a crossing edge.

        The assertions prove one rotated courtyard fits and one translated copy
        does not. They do not prove clearance from neighbouring parts or the
        exact shape of KiCad's generated courtyard graphics.
        """
        outline = BoardOutline(20, 10)
        # A 90-degree rotation swaps the courtyard's 8 mm and 2 mm extents.
        # This proves the rotated 2 mm horizontal by 8 mm vertical box fits.
        self.assertTrue(outline.contains(Placement(0, 0, 90), Courtyard(8, 2)))
        # This proves a 9.1 mm centre offset leaves the rotated box beyond x=10.
        self.assertFalse(outline.contains(Placement(9.1, 0, 90), Courtyard(8, 2)))
