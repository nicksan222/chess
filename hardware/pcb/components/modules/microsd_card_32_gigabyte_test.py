"""Purchasing identity for the off-board MicroSdCard32Gigabyte."""

import unittest

from pcb.components.modules.microsd_card_32_gigabyte import MicroSdCard32Gigabyte


class MicroSdCard32GigabyteTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = MicroSdCard32Gigabyte(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "SDSQQNR-032G-GN6IA")
