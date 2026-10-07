"""Check the bought harness against the actual composed board's pin maps."""

import unittest
from dataclasses import replace

from pcb.board.board import Board
from pcb.harness.base.connections import NetConnection
from shared.electronics.harness import HARNESSES, validate_harness_connections


class HarnessConnectionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pin_nets = {
            (endpoint.reference, endpoint.pin): connection.net.label
            for component in Board().components()
            for endpoint, connection in component.pin_connections()
            if isinstance(connection, NetConnection)
        }
        self.wires = tuple(wire for wires in HARNESSES.values() for wire in wires)

    def test_all_eight_wires_close_the_electrical_contract(self) -> None:
        self.assertEqual(len(self.wires), 8)
        validate_harness_connections(self.pin_nets, self.wires)

    def test_swapped_clock_data_or_power_ground_are_rejected(self) -> None:
        for connector, left, right in (("J2", "3", "4"), ("J4", "1", "2")):
            with self.subTest(connector=connector):
                wrong = self.pin_nets.copy()
                wrong[connector, left], wrong[connector, right] = (
                    wrong[connector, right],
                    wrong[connector, left],
                )
                with self.assertRaisesRegex(ValueError, "board net"):
                    validate_harness_connections(wrong, self.wires)

    def test_wrong_far_terminal_is_rejected_even_when_board_pin_matches(self) -> None:
        clock = next(wire for wire in self.wires if wire.net == "I2C_SCL")
        with self.assertRaisesRegex(ValueError, "far terminal"):
            validate_harness_connections(
                self.pin_nets, (replace(clock, far_terminal="SDA"),)
            )

    def test_duplicate_same_net_far_terminal_and_missing_wire_are_rejected(
        self,
    ) -> None:
        wrong = tuple(
            replace(wire, far_part="OLED_MODULE", far_terminal="GND")
            if wire.connector == "J4" and wire.net == "GND"
            else wire
            for wire in self.wires
        )
        with self.assertRaisesRegex(ValueError, "duplicate harness far terminal"):
            validate_harness_connections(self.pin_nets, wrong)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate_harness_connections(self.pin_nets, self.wires[:-1])
