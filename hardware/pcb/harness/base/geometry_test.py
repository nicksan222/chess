"""Tests beside placement and courtyard declarations."""

import unittest

from pcb.harness.base.geometry import Courtyard, Placement, Side, courtyards_overlap


class GeometryTest(unittest.TestCase):
    """Prove placement inputs are finite and courtyards are usable clearances."""

    def test_rejects_nonfinite_position(self) -> None:
        """NaN coordinates are rejected before a placement can be used."""
        with self.assertRaisesRegex(ValueError, "finite"):
            Placement(float("nan"), 0.0)

    def test_rejects_nonpositive_courtyard(self) -> None:
        """A zero-sized keep-clear rectangle is rejected."""
        with self.assertRaisesRegex(ValueError, "positive"):
            Courtyard(0.0, 2.0)

    def test_keeps_explicit_board_side(self) -> None:
        """The author-selected board face survives construction."""
        self.assertIs(Placement(1.0, 2.0, side=Side.BOTTOM).side, Side.BOTTOM)

    def test_rejects_invalid_side(self) -> None:
        """A string that merely resembles a side is not accepted."""
        with self.assertRaisesRegex(ValueError, "Side"):
            Placement(0.0, 0.0, side="underside")  # type: ignore[arg-type]

    def test_rejects_infinite_rotation(self) -> None:
        """Infinite rotation cannot enter the geometry model."""
        with self.assertRaisesRegex(ValueError, "finite"):
            Placement(0.0, 0.0, rotation_degrees=float("inf"))

    def test_rejects_nan_courtyard(self) -> None:
        """NaN courtyard dimensions are rejected."""
        with self.assertRaisesRegex(ValueError, "finite"):
            Courtyard(float("nan"), 2.0)

    def test_courtyard_overlap_checks_rotation_not_only_bounding_boxes(self) -> None:
        """Diagonal slim parts can share an axis-aligned box without touching."""
        box = Courtyard(4, 0.5)
        self.assertFalse(
            courtyards_overlap(Placement(0, 0, 45), box, Placement(0, 2, 45), box)
        )
        self.assertTrue(
            courtyards_overlap(Placement(0, 0, 45), box, Placement(0, 0.3, 45), box)
        )

    def test_touching_courtyards_and_opposite_board_sides_are_allowed(self) -> None:
        """A shared boundary leaves no overlap; board faces are independent."""
        box = Courtyard(2, 1)
        self.assertFalse(courtyards_overlap(Placement(0, 0), box, Placement(2, 0), box))
        self.assertFalse(
            courtyards_overlap(
                Placement(0, 0), box, Placement(0, 0, side=Side.BOTTOM), box
            )
        )
