"""Native pad and logical-pin regression checks for BSS138LT1G."""

import unittest

import pcbnew

from pcb.components.mosfets.led_switch_driver_mosfet import LedSwitchDriverMosfet
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class LedSwitchDriverMosfetTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            LedSwitchDriverMosfet,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            gate=Nets.A,
            source=Nets.B,
            drain=Nets.A,
        )
        self.assertEqual(component.definition.product.part_number, "BSS138LT1G")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("3", 0.0, 0.975, 0.56, 0.95, 0.0, 2, "A"),
            ("2", 0.95, -0.975, 0.56, 0.95, 0.0, 2, "B"),
            ("1", -0.95, -0.975, 0.56, 0.95, 0.0, 1, "A"),
        )
        self.assertEqual(set(pads), {row[0] for row in expected})
        for number, x, y, width, height, drill, shape, net in expected:
            with self.subTest(pad=number):
                pad = pads[number]
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().x), 80 + x, places=5
                )
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().y), 80 - y, places=5
                )
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().x), width, places=5)
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().y), height, places=5)
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetDrillSize().x), drill, places=5
                )
                self.assertEqual(pad.GetShape(), shape)
                self.assertEqual(pad.GetNetname(), net)
