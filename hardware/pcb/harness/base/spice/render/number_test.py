"""Prove declared numeric values survive conversion to SPICE text."""

import unittest

from pcb.harness.base.spice.render.number import spice_number


class SpiceNumberTest(unittest.TestCase):
    def test_float_round_trips_without_six_digit_rounding(self) -> None:
        """Close voltage limits must remain distinct in the generated deck."""
        for value in (1.0000001, 1.0000002, 1e-12, 3.3):
            with self.subTest(value=value):
                self.assertEqual(float(spice_number(value)), value)

    def test_integer_input_keeps_compact_spice_literal(self) -> None:
        """An exact whole-number declaration need not gain decimal noise."""
        self.assertEqual(spice_number(1000), "1000")
