"""Purchasing identity for the off-board PanelDcBarrelJack."""

import unittest

from pcb.components.connectors.panel_dc_barrel_jack import PanelDcBarrelJack


class PanelDcBarrelJackTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = PanelDcBarrelJack(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "722A")
