"""Purchasing identity for the off-board OledHarnessCrimpContact."""

import unittest

from pcb.components.connectors.oled_harness_crimp_contact import OledHarnessCrimpContact


class OledHarnessCrimpContactTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = OledHarnessCrimpContact(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "SSH-003T-P0.2-H")
