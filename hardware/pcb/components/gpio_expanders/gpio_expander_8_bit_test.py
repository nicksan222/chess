"""Native pad and logical-pin regression checks for TCA9554DWR."""

import unittest

import pcbnew

from pcb.components.gpio_expanders.gpio_expander_8_bit import GpioExpander8Bit
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class GpioExpander8BitTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            GpioExpander8Bit,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            address_0=Nets.A,
            address_1=Nets.B,
            address_2=Nets.A,
            p0=Nets.B,
            p1=Nets.A,
            p2=Nets.B,
            p3=Nets.A,
            ground=Nets.B,
            p4=Nets.A,
            p5=Nets.B,
            p6=Nets.A,
            p7=Nets.B,
            interrupt=Nets.A,
            i2c_clock=Nets.B,
            i2c_data=Nets.A,
            supply=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "TCA9554DWR")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("9", 4.65, -4.445, 2.0, 0.6, 0.0, 2, "A"),
            ("10", 4.65, -3.175, 2.0, 0.6, 0.0, 2, "B"),
            ("11", 4.65, -1.904999, 2.0, 0.6, 0.0, 2, "A"),
            ("12", 4.65, -0.634999, 2.0, 0.6, 0.0, 2, "B"),
            ("13", 4.65, 0.635, 2.0, 0.6, 0.0, 2, "A"),
            ("14", 4.65, 1.905, 2.0, 0.6, 0.0, 2, "B"),
            ("15", 4.65, 3.175, 2.0, 0.6, 0.0, 2, "A"),
            ("16", 4.65, 4.445, 2.0, 0.6, 0.0, 2, "B"),
            ("8", -4.65, -4.445, 2.0, 0.6, 0.0, 2, "B"),
            ("7", -4.65, -3.175, 2.0, 0.6, 0.0, 2, "A"),
            ("6", -4.65, -1.904999, 2.0, 0.6, 0.0, 2, "B"),
            ("5", -4.65, -0.634999, 2.0, 0.6, 0.0, 2, "A"),
            ("4", -4.65, 0.635, 2.0, 0.6, 0.0, 2, "B"),
            ("3", -4.65, 1.905, 2.0, 0.6, 0.0, 2, "A"),
            ("2", -4.65, 3.175, 2.0, 0.6, 0.0, 2, "B"),
            ("1", -4.65, 4.445, 2.0, 0.6, 0.0, 1, "A"),
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
