"""Purchasing identity for the off-board PowerHarnessCrimpContact."""

import unittest

from pcb.components.connectors.power_harness_crimp_contact import (
    PowerHarnessCrimpContact,
)


class PowerHarnessCrimpContactTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = PowerHarnessCrimpContact(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "SVH-21T-P1.1")
