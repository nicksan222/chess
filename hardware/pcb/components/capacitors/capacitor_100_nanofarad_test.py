"""Electrical and physical checks for the board's exact 100 nF capacitor."""

import unittest

import pcbnew

from pcb.components.capacitors.capacitor_100_nanofarad import Capacitor100Nanofarad
from pcb.harness import BoardOutline, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    SIGNAL = "SIGNAL"
    GROUND = "GND"


class Capacitor100NanofaradTest(unittest.TestCase):
    def test_fixed_product_and_value_drive_the_simulation(self) -> None:
        board = Circuit(Nets)
        capacitor = board.place(
            Capacitor100Nanofarad,
            reference="C1",
            placement=Placement(0, 0),
            purpose="decoupling",
            terminal_a=Nets.SIGNAL,
            terminal_b=Nets.GROUND,
        )
        self.assertEqual(capacitor.definition.product.part_number, "CC0603KRX7R9BB104")
        self.assertEqual(capacitor.rated_volts, 50)
        with board.check(
            "nominal", ground=Nets.GROUND, purpose="capacitor AC response"
        ) as check:
            check.ac_sweep(start_hz=1000, stop_hz=10000, points_per_decade=10)
            supply = check.dc_supply(
                "V1", Nets.SIGNAL, Nets.GROUND, volts=0, ac_volts=1
            )
            check.source_current(
                supply,
                between=(0.00627, 0.00630),
                because="100 nF at 10 kHz and 1 V has about 6.283 mA current magnitude",
            )
        self.assertAlmostEqual(
            board.run("nominal")["result_board_0"], 0.0062831853, places=6
        )

    def test_native_pads_match_the_production_ceramic_land(self) -> None:
        board = Circuit(Nets, outline=BoardOutline(10, 10))
        board.place(
            Capacitor100Nanofarad,
            reference="C1",
            placement=Placement(0, 0),
            purpose="decoupling",
            terminal_a=Nets.SIGNAL,
            terminal_b=Nets.GROUND,
        )
        native = render_board(board)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        self.assertEqual(set(pads), {"1", "2"})
        for number, x_mm, net in (("1", 4.325, "SIGNAL"), ("2", 5.675, "GND")):
            pad = pads[number]
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetPosition().x), x_mm)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetPosition().y), 5)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().x), 0.65)
            self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().y), 0.7)
            self.assertEqual(pad.GetShape(), pcbnew.PAD_SHAPE_RECT)
            self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_SMD)
            self.assertEqual(pad.GetNetname(), net)
