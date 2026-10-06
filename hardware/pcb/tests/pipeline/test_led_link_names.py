"""Existing LED links retain their published net identities.

Protects the `led_link_names` contract: a hop that already had a published net name
must keep it (renaming would silently rename nets), while a hop with no published
name gets the generated endpoint-based one.
"""

import unittest

from pcb.definition.assemblies import led_link_names
from shared.hall_banks import SquarePosition


class LedLinkNamesTest(unittest.TestCase):
    def test_existing_link_keeps_published_names(self) -> None:
        self.assertEqual(
            led_link_names.for_squares(
                SquarePosition.parse("A1"), SquarePosition.parse("B1")
            ),
            ("N$207", "N$208"),
        )

    def test_new_link_has_readable_names(self) -> None:
        # A1 -> H8 is not a real chain hop; it only exercises the fallback naming.
        self.assertEqual(
            led_link_names.for_squares(
                SquarePosition.parse("A1"), SquarePosition.parse("H8")
            ),
            ("LED_DATA_A1_TO_H8", "LED_CLOCK_A1_TO_H8"),
        )
