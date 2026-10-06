"""Purchasing identity for the off-board OledDisplayModule."""

import unittest

from pcb.components.modules.oled_display_module import OledDisplayModule


class OledDisplayModuleTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = OledDisplayModule(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "A 1-9")
