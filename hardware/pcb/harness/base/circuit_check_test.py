"""Edge checks for the staged circuit-check authoring context."""

import unittest

from pcb.harness import Circuit, Net


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"


class CircuitCheckTest(unittest.TestCase):
    """Prove staged checks commit atomically and keep sources local."""

    def test_supply_handle_cannot_be_measured_in_another_check(self) -> None:
        """A source handle can only be observed by its declaring scenario."""
        board = Circuit(Nets)
        first = board.check("first", ground=Nets.GROUND, purpose="first setup")
        second = board.check("second", ground=Nets.GROUND, purpose="other setup")
        supply = first.dc_supply("V1", Nets.POWER, Nets.GROUND, volts=3.3)
        # The assertion must describe a stimulus in its own test setup.
        with self.assertRaisesRegex(ValueError, "this check"):
            second.source_current(supply, between=(0, 1), because="wrong supply")

    def test_failed_check_cannot_be_mutated_after_leaving_context(self) -> None:
        """A failed context closes permanently instead of becoming a check later."""
        board = Circuit(Nets)
        check = board.check("incomplete", ground=Nets.GROUND, purpose="unfinished")
        with self.assertRaisesRegex(ValueError, "expectation"), check:
            check.dc_supply("V1", Nets.POWER, Nets.GROUND, volts=3.3)
        # A failed context stays closed; late declarations cannot silently
        # turn that failed test into a registered passing test.
        with self.assertRaisesRegex(ValueError, "already closed"):
            check.dc_supply("V2", Nets.POWER, Nets.GROUND, volts=3.3)
