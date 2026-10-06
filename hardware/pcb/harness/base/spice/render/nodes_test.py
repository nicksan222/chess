"""Tests beside conversion of board net names to safe SPICE node names."""

import unittest

from pcb.harness.base.net import Net
from pcb.harness.base.spice.render.nodes import NodeMap


class Nets(Net):
    GROUND = "GND"
    POWER = "+3V3"
    SENSE_A1 = "SENSE-A1"
    A_DASH_B = "A-B"
    A_B = "A_B"
    MISSING = "MISSING"


class OtherNets(Net):
    GROUND = "GND"


class NodeMapTest(unittest.TestCase):
    def test_rejects_nets_from_two_enum_types(self) -> None:
        with self.assertRaisesRegex(ValueError, "one Net enum"):
            NodeMap((Nets.GROUND, OtherNets.GROUND), Nets.GROUND)

    def test_ground_becomes_spice_zero_and_other_nets_are_distinct(self) -> None:
        nodes = NodeMap((Nets.GROUND, Nets.POWER, Nets.SENSE_A1), Nets.GROUND)
        self.assertEqual(nodes.node(Nets.GROUND), "0")
        self.assertNotEqual(nodes.node(Nets.POWER), nodes.node(Nets.SENSE_A1))

    def test_unknown_net_is_rejected(self) -> None:
        nodes = NodeMap((Nets.GROUND, Nets.POWER), Nets.GROUND)
        with self.assertRaisesRegex(ValueError, "unknown net"):
            nodes.node(Nets.MISSING)

    def test_names_that_would_sanitize_identically_stay_distinct(self) -> None:
        nodes = NodeMap((Nets.GROUND, Nets.A_DASH_B, Nets.A_B), Nets.GROUND)
        self.assertNotEqual(nodes.node(Nets.A_DASH_B), nodes.node(Nets.A_B))

    def test_missing_ground_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown ground"):
            NodeMap((Nets.POWER,), Nets.GROUND)
