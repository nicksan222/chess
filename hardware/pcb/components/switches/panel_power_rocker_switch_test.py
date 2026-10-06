"""Purchasing identity for the off-board PanelPowerRockerSwitch."""

import unittest

from pcb.components.switches.panel_power_rocker_switch import PanelPowerRockerSwitch


class PanelPowerRockerSwitchTest(unittest.TestCase):
    def test_assembly_instance_selects_the_approved_product(self) -> None:
        part = PanelPowerRockerSwitch(reference="ASSEMBLY1")
        self.assertEqual(part.reference, "ASSEMBLY1")
        self.assertEqual(part.product.mpn, "RA11131100")
