"""Concrete catalog completeness against the authoritative purchasing contract."""

import unittest

from pcb.components.catalog import ASSEMBLY_PRODUCTS, PCB_DEFINITIONS
from shared.components import COMPONENTS


class CatalogTest(unittest.TestCase):
    def test_every_approved_product_has_exactly_one_concrete_definition(self) -> None:
        keys = [definition.product.key for definition in PCB_DEFINITIONS]
        keys.extend(product.key for product in ASSEMBLY_PRODUCTS)
        self.assertEqual(len(keys), len(set(keys)))
        # Wire spools stay in the purchasing/harness contract. They are not
        # electrical component classes or a separate connection layer.
        component_keys = {
            key
            for key in COMPONENTS
            if not key.startswith(("POWER_HARNESS_WIRE_", "OLED_HARNESS_WIRE_"))
        }
        self.assertEqual(set(keys), component_keys)
