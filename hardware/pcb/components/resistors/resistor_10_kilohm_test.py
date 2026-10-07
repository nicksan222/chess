"""Electrical and physical checks for the board's exact 10000 ohm resistor."""

import unittest

import pcbnew

from pcb.components.resistors.resistor_10_kilohm import Resistor10Kilohm
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    SIGNAL = "SIGNAL"
    GROUND = "GND"


class Resistor10KilohmTest(unittest.TestCase):
    def test_fixed_product_and_value_drive_the_simulation(self) -> None:
        board = Circuit(Nets)
        resistor = board.place(
            Resistor10Kilohm,
            reference="R9",
            placement=Placement(0, 0),
            purpose="bias resistor",
            terminal_a=Nets.SIGNAL,
            terminal_b=Nets.GROUND,
        )
        self.assertEqual(resistor.definition.product.part_number, "RC0603FR-0710KL")
        self.assertEqual(resistor.tolerance_percent, 1)
        with board.check("nominal", ground=Nets.GROUND, purpose="Ohm's law") as check:
            supply = check.dc_supply("V1", Nets.SIGNAL, Nets.GROUND, volts=3.3)
            check.source_current(
                supply,
                between=(-0.000331, -0.000329),
                because="3.3 V across 10000 ohms draws about 58.93 mA",
            )
        self.assertAlmostEqual(
            board.run("nominal")["result_board_0"], -3.3 / 10000, places=6
        )

    def test_native_pads_match_the_reviewed_yageo_land(self) -> None:
        board = Circuit(Nets, outline=BoardOutline(10, 10))
        board.place(
            Resistor10Kilohm,
            reference="R9",
            placement=Placement(0, 0),
            purpose="bias resistor",
            terminal_a=Nets.SIGNAL,
            terminal_b=Nets.GROUND,
        )
        native = render_board(board)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        self.assertEqual(set(pads), {"1", "2"})
        for number, x_mm, net in (("1", 4.15, "SIGNAL"), ("2", 5.85, "GND")):
            pad = pads[number]
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetPosition().x), x_mm)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetPosition().y), 5)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().x), 0.9)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().y), 0.8)
            self.assertEqual(pad.GetShape(), pcbnew.PAD_SHAPE_RECT)
            self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_SMD)
            self.assertEqual(pad.GetNetname(), net)
