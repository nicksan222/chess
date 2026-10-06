"""Check deterministic ordering of serialized KiCad footprint blocks."""

import unittest

from pcb.harness.base.pcbnew.render.order import order_footprints


class OrderFootprintsTest(unittest.TestCase):
    def test_sorts_only_top_level_footprints_by_reference(self) -> None:
        """Object insertion order must not change the reviewed board file."""
        first = '(footprint "" (property "Reference" "R1") (at 1 2))'
        second = '(footprint "" (property "Reference" "R2") (at 3 4))'
        source = f'(kicad_pcb\n\t(net 1 "MID")\n\t{second}\n\t{first}\n\t(segment (net 1))\n)'
        expected = f'(kicad_pcb\n\t(net 1 "MID")\n\t{first}\n\t{second}\n\t(segment (net 1))\n)'
        self.assertEqual(order_footprints(source), expected)

    def test_parentheses_and_escaped_quotes_inside_strings_do_not_end_block(
        self,
    ) -> None:
        """A footprint value containing syntax characters stays intact."""
        first = '(footprint "(special)" (property "Reference" "R1") (property "Value" "a \\" b (c)"))'
        second = '(footprint "" (property "Reference" "R2"))'
        source = f"(kicad_pcb\n\t{second}\n\t{first}\n)"
        self.assertEqual(
            order_footprints(source), f"(kicad_pcb\n\t{first}\n\t{second}\n)"
        )

    def test_duplicate_reference_is_rejected(self) -> None:
        """An ambiguous component identity cannot produce a canonical file."""
        source = '(kicad_pcb (footprint "" (property "Reference" "R1")) (footprint "" (property "Reference" "R1")))'
        with self.assertRaisesRegex(ValueError, "duplicate footprint reference"):
            order_footprints(source)

    def test_missing_reference_is_rejected(self) -> None:
        """Every serialized footprint needs a stable sorting identity."""
        with self.assertRaisesRegex(ValueError, "missing Reference"):
            order_footprints('(kicad_pcb (footprint ""))')

    def test_unbalanced_board_is_rejected(self) -> None:
        """Malformed serialization must never be silently rewritten."""
        with self.assertRaisesRegex(ValueError, "unbalanced"):
            order_footprints('(kicad_pcb (footprint "" (property "Reference" "R1"))')
