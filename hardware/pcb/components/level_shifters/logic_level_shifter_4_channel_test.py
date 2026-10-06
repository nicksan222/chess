"""Native pad and logical-pin regression checks for SN74AHCT125DR."""

import unittest

import pcbnew

from pcb.components.level_shifters.logic_level_shifter_4_channel import (
    LogicLevelShifter4Channel,
)
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class LogicLevelShifter4ChannelTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            LogicLevelShifter4Channel,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            buffer_1_output_enable=Nets.A,
            buffer_1_input=Nets.B,
            buffer_1_output=Nets.A,
            buffer_2_output_enable=Nets.B,
            buffer_2_input=Nets.A,
            buffer_2_output=Nets.B,
            ground=Nets.A,
            buffer_3_output=Nets.B,
            buffer_3_input=Nets.A,
            buffer_3_output_enable=Nets.B,
            buffer_4_output=Nets.A,
            buffer_4_input=Nets.B,
            buffer_4_output_enable=Nets.A,
            supply=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "SN74AHCT125DR")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("8", 2.7, -3.81, 1.55, 0.6, 0.0, 2, "B"),
            ("9", 2.7, -2.539999, 1.55, 0.6, 0.0, 2, "A"),
            ("10", 2.7, -1.27, 1.55, 0.6, 0.0, 2, "B"),
            ("11", 2.7, -0.0, 1.55, 0.6, 0.0, 2, "A"),
            ("12", 2.7, 1.27, 1.55, 0.6, 0.0, 2, "B"),
            ("13", 2.7, 2.54, 1.55, 0.6, 0.0, 2, "A"),
            ("14", 2.7, 3.81, 1.55, 0.6, 0.0, 2, "B"),
            ("7", -2.7, -3.81, 1.55, 0.6, 0.0, 2, "A"),
            ("6", -2.7, -2.539999, 1.55, 0.6, 0.0, 2, "B"),
            ("5", -2.7, -1.27, 1.55, 0.6, 0.0, 2, "A"),
            ("4", -2.7, -0.0, 1.55, 0.6, 0.0, 2, "B"),
            ("3", -2.7, 1.27, 1.55, 0.6, 0.0, 2, "A"),
            ("2", -2.7, 2.54, 1.55, 0.6, 0.0, 2, "B"),
            ("1", -2.7, 3.81, 1.55, 0.6, 0.0, 1, "A"),
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
