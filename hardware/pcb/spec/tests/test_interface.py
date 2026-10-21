"""The board interface the PCB publishes for the case and plate.

The export is the enclosure's only view of the board, so it must round-trip
exactly, refuse a different shape, and carry the facts the case is built around.
"""

import json
import unittest
from dataclasses import asdict
from typing import cast

from pcb.board.interface import BoardInterface, decode
from pcb.spec.electronics.harness import HARNESSES


class BoardInterfaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.interface = BoardInterface.current()

    def written(self) -> dict[str, object]:
        """The interface as the export writes and a reader parses it."""
        return cast(dict[str, object], json.loads(json.dumps(asdict(self.interface))))

    def test_json_round_trip_is_exact(self) -> None:
        self.assertEqual(decode(BoardInterface, self.written()), self.interface)

    def test_a_different_shape_is_refused(self) -> None:
        raw = self.written()
        raw["case_height_mm"] = 30.0
        with self.assertRaisesRegex(ValueError, "case_height_mm"):
            _ = decode(BoardInterface, raw)
        raw = self.written()
        raw["pcb_size_mm"] = [320.0, 380.0]
        with self.assertRaisesRegex(ValueError, "expected 3 values"):
            _ = decode(BoardInterface, raw)
        raw = self.written()
        del raw["jack"]
        with self.assertRaises(TypeError):
            _ = decode(BoardInterface, raw)

    def test_exported_board_facts_are_the_agreed_values(self) -> None:
        # Written out on purpose: these are what the case and plate are built
        # around, so changing one is an interface change to review with CAD.
        board = self.interface
        self.assertEqual(board.grid_count, 8)
        self.assertEqual(board.square_size_mm, 40.0)
        self.assertEqual(board.pcb_size_mm, (320.0, 380.0, 1.6))
        self.assertEqual(board.pcb_center_offset_y_mm, -30.0)
        self.assertEqual(board.panel_origin_y_mm, -190.0)
        self.assertEqual(board.led_offset_mm, (13.0, 13.0))
        self.assertEqual(len(board.mounting_holes_mm), 20)
        self.assertEqual(board.mounting_hole_diameter_mm, 3.4)
        self.assertEqual(len(board.expanders_mm), 8)
        a1 = next(square for square in board.squares if square.name == "A1")
        self.assertEqual((a1.row, a1.column, a1.is_dark), (7, 0, True))
        self.assertEqual(a1.centre_mm, (-140.0, -140.0))
        self.assertEqual(a1.led_position_mm, (-127.0, -127.0))
        self.assertEqual(board.host.centre_mm, (123.0, -63.5))
        self.assertEqual(board.host.rotation_degrees, 180.0)
        self.assertAlmostEqual(board.host.board_to_board_mm, 11.04)
        self.assertEqual(board.host.unverified, ("sd_socket_mm", "sd_socket_height_mm"))
        self.assertEqual(board.display.body_mm, (72.0, 43.0, 6.25))
        self.assertEqual(board.display.pads_mm["GND"], (-33.5, -3.81))
        self.assertEqual(board.display.pads_mm["RES"], (-33.5, 6.35))
        self.assertEqual(board.jack.bushing_diameter_mm, 7.94)
        self.assertEqual(board.jack.flange_diameter_mm, 11.0)
        self.assertEqual(board.rocker.cutout_mm, (19.4, 13.0))
        self.assertEqual(board.button_actuator_diameter_mm, 3.5)

    def test_harness_carries_every_wire_with_its_context(self) -> None:
        board = self.interface
        self.assertEqual(
            len(board.harness), sum(len(wires) for wires in HARNESSES.values())
        )
        self.assertEqual(
            {(wire.harness, wire.connector) for wire in board.harness},
            {("Power entry", "J4"), ("OLED", "J2")},
        )
        for wire in board.harness:
            with self.subTest(cavity=(wire.connector, wire.cavity)):
                if wire.far_part == "OLED_MODULE":
                    self.assertIn(wire.far_terminal, board.display.pads_mm)
                    self.assertEqual(wire.far_termination, "solder to pad")


if __name__ == "__main__":
    unittest.main()
