"""Tests beside the product identity contract."""

import unittest

from pcb.harness.base.product import Product


class ProductTest(unittest.TestCase):
    """Prove every product carries purchase identity and physical dimensions."""

    def test_rejects_a_missing_datasheet(self) -> None:
        """A product without evidence cannot be defined."""
        with self.assertRaisesRegex(ValueError, "datasheet"):
            Product("R", "Maker", "R-1", "0603", (1.6, 0.8, 0.5), "")

    def test_rejects_a_body_without_three_positive_dimensions(self) -> None:
        """The body requires exactly three positive dimensions."""
        with self.assertRaisesRegex(ValueError, "three positive"):
            Product("R", "Maker", "R-1", "0603", (1.6, 0.8, 0.0), "sheet")

    def test_rejects_nonfinite_body_dimension(self) -> None:
        """Infinite body dimensions are rejected as unusable facts."""
        with self.assertRaisesRegex(ValueError, "three positive"):
            Product("R", "Maker", "R-1", "0603", (1.6, float("inf"), 0.5), "sheet")

    def test_rejects_whitespace_only_part_number(self) -> None:
        """Whitespace cannot stand in for a purchased part number."""
        with self.assertRaisesRegex(ValueError, "identity"):
            Product("R", "Maker", "  ", "0603", (1.6, 0.8, 0.5), "sheet")
