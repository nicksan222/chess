"""Native pad and logical-pin regression checks for SK9822-A."""

import unittest

import pcbnew

from pcb.components.leds.clocked_rgb_led import ClockedRgbLed
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class ClockedRgbLedTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            ClockedRgbLed,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            data_in=Nets.A,
            clock_in=Nets.B,
            ground=Nets.A,
            five_volts=Nets.B,
            clock_out=Nets.A,
            data_out=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "SK9822-A")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("6", -2.6, -1.6, 1.8, 1.2, 0.0, 2, "B"),
            ("5", -2.6, -0.0, 1.8, 1.2, 0.0, 2, "A"),
            ("4", -2.6, 1.6, 1.8, 1.2, 0.0, 2, "B"),
            ("3", 2.6, 1.6, 1.8, 1.2, 0.0, 2, "A"),
            ("2", 2.6, -0.0, 1.8, 1.2, 0.0, 2, "B"),
            ("1", 2.6, -1.6, 1.8, 1.2, 0.0, 1, "A"),
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
