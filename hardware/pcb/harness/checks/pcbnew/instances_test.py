"""Repeated placements remain separate, individually selectable components."""

import unittest
from dataclasses import replace

from pcb.board.board import Board
from shared.electronics.hall_sensor import HallSensorPin


class InstancesTest(unittest.TestCase):
    def test_sensor_selection_reads_its_own_pin_map(self) -> None:
        board = Board()
        first, last = board.sensors["A1"], board.sensors["H8"]
        self.assertIsNot(first, last)
        self.assertIs(board.sensor("A1"), first)
        self.assertIs(first.definition, last.definition)
        self.assertNotEqual(
            first.net(HallSensorPin.ACTIVE_LOW_OUTPUT),
            last.net(HallSensorPin.ACTIVE_LOW_OUTPUT),
        )
        self.assertIn(first, board.components())
        self.assertIn(last, board.components())
        self.assertIsNot(board.sensor_bypasses["A1"], board.sensor_bypasses["H8"])
        self.assertNotEqual(
            board.input_bulk_capacitor.reference, board.host_bulk_capacitor.reference
        )

    def test_one_sensor_can_have_its_own_route_choice(self) -> None:
        board = Board()
        target = board.sensors["A1"].net(HallSensorPin.ACTIVE_LOW_OUTPUT)
        neighbour = board.sensors["B1"].net(HallSensorPin.ACTIVE_LOW_OUTPUT)
        board.wiring = tuple(
            replace(route, width_mm=0.4) if route.net == target else route
            for route in board.wiring
        )
        self.assertEqual(
            next(route.width_mm for route in board.wiring if route.net == target), 0.4
        )
        self.assertEqual(
            next(route.width_mm for route in board.wiring if route.net == neighbour),
            0.31,
        )
        self.assertEqual(
            board.sensors["A1"].net(HallSensorPin.ACTIVE_LOW_OUTPUT), target
        )
        with self.assertRaisesRegex(ValueError, "unknown square"):
            board.sensor("Z9")
