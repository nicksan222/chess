"""Purchasing identity for the off-board RaspberryPiZero2W."""

import unittest

from pcb.components.modules.raspberry_pi_zero_2_w import RaspberryPiZero2W


class RaspberryPiZero2WTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = RaspberryPiZero2W(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "SC0510")
