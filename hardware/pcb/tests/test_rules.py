"""The chosen geometry has to be inside what the fab can make.

There is no design-rule checker here, so these numbers and these assertions are
the whole guarantee. They are worth exactly what they say and no more: they
confirm the geometry is manufacturable, not that the layout is correct.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from core import rules


class CapabilityTest(unittest.TestCase):
    def test_traces_are_well_inside_the_process(self) -> None:
        self.assertGreaterEqual(rules.TRACE_WIDTH_MM, rules.PCBWAY_MIN_TRACE_WIDTH_MM)
        self.assertGreaterEqual(rules.CLEARANCE_MM, rules.PCBWAY_MIN_CLEARANCE_MM)

    def test_a_hand_soldered_board_keeps_a_wide_margin(self) -> None:
        """Near a process limit is the wrong place for a prototype to be."""
        self.assertGreaterEqual(
            round(rules.TRACE_WIDTH_MM, 6),
            round(3.0 * rules.PCBWAY_MIN_TRACE_WIDTH_MM, 6),
        )
        self.assertGreaterEqual(
            round(rules.CLEARANCE_MM, 6),
            round(3.0 * rules.PCBWAY_MIN_CLEARANCE_MM, 6),
        )

    def test_power_carries_more_copper_than_signal(self) -> None:
        self.assertGreater(rules.POWER_TRACE_WIDTH_MM, rules.TRACE_WIDTH_MM)

    def test_vias_are_drillable_with_a_real_ring(self) -> None:
        self.assertGreaterEqual(rules.VIA_DRILL_MM, rules.PCBWAY_MIN_DRILL_MM)
        ring = rules.annular_ring(rules.VIA_PAD_MM, rules.VIA_DRILL_MM)
        self.assertGreaterEqual(ring, rules.PCBWAY_MIN_ANNULAR_RING_MM)

    def test_a_pour_pulls_back_further_than_a_signal(self) -> None:
        self.assertGreaterEqual(rules.POUR_CLEARANCE_MM, rules.CLEARANCE_MM)

    def test_silkscreen_is_printable(self) -> None:
        self.assertGreaterEqual(rules.SILK_LINE_MM, rules.PCBWAY_MIN_SILK_LINE_MM)
        self.assertGreaterEqual(
            rules.SILK_TEXT_HEIGHT_MM, rules.PCBWAY_MIN_SILK_TEXT_HEIGHT_MM
        )


class DerivedGeometryTest(unittest.TestCase):
    def test_a_hole_clears_the_lead_it_takes(self) -> None:
        for lead in (0.5, 0.64, 0.8, 1.5):
            drill = rules.drill_for_lead(lead)
            self.assertGreater(drill, lead)
            self.assertGreaterEqual(drill, rules.PCBWAY_MIN_DRILL_MM)

    def test_a_pad_gives_the_design_ring_around_its_hole(self) -> None:
        for lead in (0.5, 0.8, 1.5):
            drill = rules.drill_for_lead(lead)
            pad = rules.pad_for_drill(drill)
            self.assertAlmostEqual(
                rules.annular_ring(pad, drill), rules.THT_ANNULAR_RING_MM, places=6
            )


class ValidationTest(unittest.TestCase):
    def test_the_module_validates_itself_on_import(self) -> None:
        rules.validate()

    def test_a_choice_outside_the_capability_is_refused(self) -> None:
        """Raising a limit must not silently produce an unmakeable board."""
        original = rules.TRACE_WIDTH_MM
        try:
            rules.TRACE_WIDTH_MM = rules.PCBWAY_MIN_TRACE_WIDTH_MM / 2.0
            with self.assertRaises(ValueError):
                rules.validate()
        finally:
            rules.TRACE_WIDTH_MM = original
        rules.validate()

    def test_a_thin_via_ring_is_refused(self) -> None:
        original = rules.VIA_PAD_MM
        try:
            rules.VIA_PAD_MM = rules.VIA_DRILL_MM + 0.01
            with self.assertRaises(ValueError):
                rules.validate()
        finally:
            rules.VIA_PAD_MM = original
        rules.validate()


if __name__ == "__main__":
    unittest.main()
