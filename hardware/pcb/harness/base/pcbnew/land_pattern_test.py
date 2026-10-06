"""Contract tests for logical-pin to physical-pad coverage.

The fixtures are deliberately tiny package examples. They prove mapping
invariants only; they do not validate a manufacturer's drawing or a rendered
KiCad footprint.
"""

import unittest
from enum import StrEnum

from pcb.harness.base.pcbnew.land_pattern import LandPattern
from pcb.harness.base.pcbnew.pad import Pad
from pcb.harness.base.pcbnew.point import Point


class Pin(StrEnum):
    """Logical contacts used by this two-pin package fixture."""

    A = "1"
    B = "2"


class LandPatternTest(unittest.TestCase):
    def test_every_logical_pin_needs_at_least_one_pad(self) -> None:
        """Missing pad coverage is rejected before a footprint can be built.

        The assertion proves the pattern reports an absent ``Pin.B``. It does
        not prove the present pad is at the correct package location.
        """
        with self.assertRaisesRegex(ValueError, "missing"):
            LandPattern(Pin, (Pad(Pin.A, Point(-1, 0), 1, 1),))

    def test_two_physical_pads_may_share_one_logical_contact(self) -> None:
        """Duplicate electrical contacts are allowed with distinct pad numbers.

        The assertion proves all three declared copper pads are retained,
        including the duplicated ``Pin.A`` contact. It does not prove those
        pads will be joined to the same native net until connections render.
        """
        pattern = LandPattern(
            Pin,
            (
                Pad(Pin.A, Point(-1, 1), 1, 1),
                Pad(Pin.A, Point(-1, -1), 1, 1, number="1b"),
                Pad(Pin.B, Point(1, 0), 1, 1),
            ),
        )
        # All three pieces of copper remain represented by the land pattern;
        # this count says nothing about their coordinates or native rendering.
        self.assertEqual(len(pattern.pads), 3)

    def test_physical_pad_numbers_must_be_unique(self) -> None:
        """Two copper lands cannot use the same KiCad pad identity.

        The assertion proves duplicate physical numbers are rejected. It does
        not check that numbers follow a particular manufacturer's numbering
        convention beyond uniqueness and the pad-number syntax contract.
        """
        with self.assertRaisesRegex(ValueError, "unique"):
            LandPattern(
                Pin,
                (
                    Pad(Pin.A, Point(-1, 0), 1, 1),
                    Pad(Pin.B, Point(1, 0), 1, 1, number="1"),
                ),
            )

    def test_non_pad_entry_is_rejected_cleanly(self) -> None:
        """A malformed package entry should not leak an attribute error."""
        with self.assertRaisesRegex(ValueError, "pads"):
            LandPattern(Pin, (object(),))  # type: ignore[arg-type]

    def test_input_pad_sequence_is_copied(self) -> None:
        """Mutating an input list cannot change a validated land pattern."""
        pads = [Pad(Pin.A, Point(-1, 0), 1, 1), Pad(Pin.B, Point(1, 0), 1, 1)]
        pattern = LandPattern(Pin, pads)  # type: ignore[arg-type]
        pads.pop()
        self.assertEqual(len(pattern.pads), 2)
