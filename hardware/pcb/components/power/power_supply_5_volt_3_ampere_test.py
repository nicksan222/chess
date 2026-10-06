"""Purchasing identity for the off-board PowerSupply5Volt3Ampere."""

import unittest

from pcb.components.power.power_supply_5_volt_3_ampere import PowerSupply5Volt3Ampere


class PowerSupply5Volt3AmpereTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = PowerSupply5Volt3Ampere(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "GST18A05-P1J")
        self.assertEqual(part.output_volts, 5.0)
        self.assertEqual(part.rated_amperes, 3.0)
