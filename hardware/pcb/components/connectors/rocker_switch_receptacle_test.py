"""Purchasing identity for the off-board RockerSwitchReceptacle."""

import unittest

from pcb.components.connectors.rocker_switch_receptacle import RockerSwitchReceptacle


class RockerSwitchReceptacleTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = RockerSwitchReceptacle(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "2-520275-2")
