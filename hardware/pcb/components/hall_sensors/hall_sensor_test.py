"""Native pad and logical-pin regression checks for DRV5032FCDBZR."""

import unittest

import pcbnew

from pcb.components.hall_sensors.hall_sensor import HallSensor
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class HallSensorTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            HallSensor,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            supply=Nets.A,
            active_low_output=Nets.B,
            ground=Nets.A,
        )
        self.assertEqual(component.definition.product.part_number, "DRV5032FCDBZR")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("3", 1.05, -0.0, 1.3, 0.6, 0.0, 2, "A"),
            ("2", -1.05, -0.95, 1.3, 0.6, 0.0, 2, "B"),
            ("1", -1.05, 0.95, 1.3, 0.6, 0.0, 1, "A"),
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
