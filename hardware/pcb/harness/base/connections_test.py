"""Tests beside pin connection declarations."""

import unittest
from typing import cast

from pcb.harness.base.connections import Endpoint, NetConnection, NoConnect
from pcb.harness.base.net import Net


class Nets(Net):
    SENSE = "SENSE"


class ConnectionTest(unittest.TestCase):
    """Prove pin links and intentional opens stay typed and reviewable."""

    def test_rejects_duplicate_exact_peer(self) -> None:
        """A peer requirement may name each endpoint only once."""
        peer = Endpoint("U2", "3")
        with self.assertRaisesRegex(ValueError, "unique"):
            NetConnection(Nets.SENSE, (peer, peer))

    def test_rejects_unexplained_open_pin(self) -> None:
        """An open physical pin must carry a human-readable reason."""
        with self.assertRaisesRegex(ValueError, "reason"):
            NoConnect("  ")

    def test_rejects_raw_net_name(self) -> None:
        """Connections accept enum members, never bare labels."""
        with self.assertRaisesRegex(ValueError, "Net enum"):
            NetConnection(cast(Net, "  "))

    def test_rejects_blank_endpoint_pin(self) -> None:
        """A peer endpoint needs both a reference and pin number."""
        with self.assertRaisesRegex(ValueError, "reference and pin"):
            Endpoint("U1", " ")

    def test_rejects_net_name_that_could_inject_a_spice_line(self) -> None:
        """Newline-containing input cannot become a generated simulator line."""
        with self.assertRaisesRegex(ValueError, "Net enum"):
            NetConnection(cast(Net, "GND\nV1 A 0 100"))
