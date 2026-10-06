"""Native pad and logical-pin regression checks for Si4403DDY-T1-GE3."""

import unittest

import pcbnew

from pcb.components.mosfets.led_power_mosfet import LedPowerMosfet
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class LedPowerMosfetTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            LedPowerMosfet,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            source=Nets.A,
            gate=Nets.B,
            drain=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "Si4403DDY-T1-GE3")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("5", 2.5275, -1.905, 1.194, 0.559, 0.0, 2, "B"),
            ("6", 2.5275, -0.635, 1.194, 0.559, 0.0, 2, "B"),
            ("7", 2.5275, 0.635, 1.194, 0.559, 0.0, 2, "B"),
            ("8", 2.5275, 1.905, 1.194, 0.559, 0.0, 2, "B"),
            ("4", -2.5275, -1.905, 1.194, 0.559, 0.0, 2, "B"),
            ("3", -2.5275, -0.635, 1.194, 0.559, 0.0, 2, "A"),
            ("2", -2.5275, 0.635, 1.194, 0.559, 0.0, 2, "A"),
            ("1", -2.5275, 1.905, 1.194, 0.559, 0.0, 1, "A"),
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
