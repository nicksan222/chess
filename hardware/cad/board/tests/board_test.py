"""The CAD assembly owns real PCB placements and fourteen printable parts."""

import unittest

from cad.board.board import Board
from cad.harness.base.pcb import PcbSnapshot
from pcb.board.board import Board as CircuitBoard
from pcb.harness import Side
from shared import dimensions


class BoardTest(unittest.TestCase):
    def test_all_pcb_components_have_one_representation(self) -> None:
        board = Board(PcbSnapshot.current())
        circuit = CircuitBoard()
        self.assertEqual(
            set(board.pcb_parts), {p.reference for p in circuit.components()}
        )
        for part in circuit.components():
            with self.subTest(reference=part.reference):
                proxy = board.pcb_parts[part.reference]
                self.assertEqual(
                    proxy.position_mm,
                    (
                        part.placement.x_mm,
                        part.placement.y_mm + dimensions.PCB_CENTER_OFFSET_Y_MM,
                    ),
                )
                self.assertEqual(
                    proxy.rotation_degrees, part.placement.rotation_degrees
                )
                self.assertEqual(proxy.body_mm, part.definition.product.body_mm)
                self.assertEqual(proxy.bottom, part.placement.side is Side.BOTTOM)

    def test_printable_parts_are_case_plate_and_button_caps(self) -> None:
        board = Board(PcbSnapshot.current())
        self.assertEqual(
            board.printable_components(), (board.case, board.plate, *board.button_caps)
        )
        self.assertEqual(board.case.reference, "Printable_Board_Case")
        self.assertEqual(board.plate.reference, "Printable_Tile_Plate")

    def test_repeated_parts_are_individual_named_instances(self) -> None:
        board = Board(PcbSnapshot.current())
        self.assertEqual(len(board.sensors), 64)
        self.assertEqual(len(board.leds), 64)
        self.assertEqual(len(board.buttons), 12)
        self.assertIsNot(board.sensors["A1"], board.sensors["B1"])
        self.assertIs(
            board.sensors["A1"], board.pcb_parts[board.pcb_definition.sensors["A1"]]
        )

    def test_off_board_parts_and_every_harness_wire_are_present(self) -> None:
        from shared.electronics.harness import HARNESSES

        board = Board(PcbSnapshot.current())
        self.assertEqual(
            {part.product_key for part in board.panel_parts},
            {"BARREL_JACK", "POWER_SWITCH"},
        )
        wires = tuple(w for group in HARNESSES.values() for w in group)
        self.assertEqual(tuple(part.wire for part in board.harness_wires), wires)
        self.assertEqual(len(board.connector_mates), 2)
        for part in board.harness_wires:
            self.assertGreater(part.route_length_mm, 0)
            self.assertLessEqual(part.route_length_mm, part.wire.length_mm)
            self.assertTrue(part.fit_check)
