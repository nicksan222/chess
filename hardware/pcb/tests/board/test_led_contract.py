"""The firmware-facing SK9822-A contract (shared/electronics/sk9822.py), S6.

Reviewer m6: the end frame supplies max(32, N/2) clocks; m2: the contract clock is
derated to 10 MHz; D1: the blank frame and the enable sequence constants exist.
"""

import unittest

from shared.electronics import sk9822


class LedContractTest(unittest.TestCase):
    """The firmware-facing LED constants and end-frame rule."""

    def test_end_frame_covers_half_a_clock_per_led(self) -> None:
        self.assertEqual(sk9822.end_frame_bits(64), 32)
        self.assertEqual(sk9822.end_frame_bits(65), 33)
        self.assertEqual(sk9822.end_frame_bits(100), 50)
        self.assertEqual(sk9822.end_frame_bits(1), 32)

    def test_clock_blank_frame_and_sequence(self) -> None:
        self.assertLessEqual(sk9822.CLOCK_HZ_MAX, 10_000_000)
        self.assertEqual(sk9822.BLANK_LED_FRAME, bytes((0xE0, 0, 0, 0)))
        self.assertEqual(sk9822.FRAME_COLOUR_ORDER, ("green", "red", "blue"))
        self.assertGreaterEqual(sk9822.LED_ENABLE_BLANKING_S, 0.010)
        self.assertEqual(sk9822.CHANNEL_AMPS_MAX, 0.018)
