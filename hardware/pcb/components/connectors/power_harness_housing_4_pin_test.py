"""Purchasing identity for the off-board PowerHarnessHousing4Pin."""

import unittest

from pcb.components.connectors.power_harness_housing_4_pin import (
    PowerHarnessHousing4Pin,
)


class PowerHarnessHousing4PinTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = PowerHarnessHousing4Pin(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "VHR-4N")
