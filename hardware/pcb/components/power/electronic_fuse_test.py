"""Native pad and logical-pin regression checks for TPS259474ARPWR."""

import unittest

import pcbnew

from pcb.components.power.electronic_fuse import ElectronicFuse
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class ElectronicFuseTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            ElectronicFuse,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            enable_uvlo=Nets.A,
            overvoltage_lockout=Nets.B,
            power_good=Nets.A,
            power_good_threshold=Nets.B,
            input=Nets.A,
            output=Nets.B,
            slew_rate=Nets.A,
            ground=Nets.B,
            current_limit=Nets.A,
            overcurrent_timer=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "TPS259474ARPWR")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("10", 0.9, 0.7, 0.6, 0.3, 0.0, 6, "B"),
            ("9", 0.9, 0.225, 0.6, 0.25, 0.0, 1, "A"),
            ("8", 0.9, -0.225, 0.6, 0.25, 0.0, 1, "B"),
            ("7", 0.9, -0.7, 0.6, 0.3, 0.0, 6, "A"),
            ("6", 0.25, -0.0, 0.3, 2.4, 0.0, 1, "B"),
            ("5", -0.25, -0.0, 0.3, 2.4, 0.0, 1, "A"),
            ("4", -0.9, -0.7, 0.6, 0.3, 0.0, 6, "B"),
            ("3", -0.9, -0.225, 0.6, 0.25, 0.0, 1, "A"),
            ("2", -0.9, 0.225, 0.6, 0.25, 0.0, 1, "B"),
            ("1", -0.9, 0.7, 0.6, 0.3, 0.0, 6, "A"),
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
