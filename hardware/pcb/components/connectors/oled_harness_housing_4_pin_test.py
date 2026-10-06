"""Purchasing identity for the off-board OledHarnessHousing4Pin."""

import unittest

from pcb.components.connectors.oled_harness_housing_4_pin import OledHarnessHousing4Pin


class OledHarnessHousing4PinTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = OledHarnessHousing4Pin(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "SHR-04V-S-B")
