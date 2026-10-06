"""Tests for board-owned, typed electrical net identities."""

import unittest
from typing import cast

from pcb.harness.base.connections import NetConnection
from pcb.harness.base.net import Net


class BoardNet(Net):
    GROUND = "GND"
    POWER = "+3V3"


class OtherBoardNet(Net):
    GROUND = "GND"


class NetTest(unittest.TestCase):
    """Prove net enums are safe, readable identities for one board."""

    def test_board_enum_has_a_readable_output_name(self) -> None:
        """The enum member exposes its generator-facing label."""
        self.assertEqual(BoardNet.POWER.label, "+3V3")

    def test_similarly_named_nets_from_different_boards_are_distinct(self) -> None:
        """Equal labels from separate enum classes do not share identity."""
        self.assertNotEqual(BoardNet.GROUND, OtherBoardNet.GROUND)

    def test_raw_string_cannot_be_used_as_connection_identity(self) -> None:
        """A raw label cannot bypass typed net identity."""
        with self.assertRaisesRegex(ValueError, "Net enum"):
            NetConnection(cast(Net, "GND"))

    def test_unsafe_net_label_is_rejected_at_enum_definition(self) -> None:
        """A label containing a generated SPICE line is rejected early."""
        with self.assertRaisesRegex(ValueError, "safe net label"):

            class UnsafeNet(Net):
                MALICIOUS = "GND\nR1 a b 1"

            self.assertEqual(UnsafeNet.MALICIOUS.label, "GND")
