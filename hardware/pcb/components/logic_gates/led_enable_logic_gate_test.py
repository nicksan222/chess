"""Native pad and logical-pin regression checks for SN74LVC1G97DBVR."""

import unittest

import pcbnew

from pcb.components.logic_gates.led_enable_logic_gate import LedEnableLogicGate
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class LedEnableLogicGateTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            LedEnableLogicGate,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            input_1=Nets.A,
            ground=Nets.B,
            input_0=Nets.A,
            output=Nets.B,
            supply=Nets.A,
            input_2=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "SN74LVC1G97DBVR")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("4", 1.3, -0.95, 1.1, 0.6, 0.0, 2, "B"),
            ("5", 1.3, -0.0, 1.1, 0.6, 0.0, 2, "A"),
            ("6", 1.3, 0.95, 1.1, 0.6, 0.0, 2, "B"),
            ("3", -1.3, -0.95, 1.1, 0.6, 0.0, 2, "A"),
            ("2", -1.3, -0.0, 1.1, 0.6, 0.0, 2, "B"),
            ("1", -1.3, 0.95, 1.1, 0.6, 0.0, 1, "A"),
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
