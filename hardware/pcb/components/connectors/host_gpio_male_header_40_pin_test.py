"""Purchasing identity for the off-board HostGpioMaleHeader40Pin."""

import unittest

from pcb.components.connectors.host_gpio_male_header_40_pin import (
    HostGpioMaleHeader40Pin,
)


class HostGpioMaleHeader40PinTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = HostGpioMaleHeader40Pin(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "PRPC020DAAN-RC")
