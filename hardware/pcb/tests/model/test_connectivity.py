"""Electrical contracts become one validated, navigable connection graph."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from base import board_placement as placement
from base import connectivity, sources
from board.wiring.nets import Net
from components.catalog import for_netlist_entry
from components.hall_sensor import HallSensor, HallSensorPin


class ConnectionGraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = sources.netlist()
        cls.placements = placement.build()
        cls.graph = connectivity.ConnectionGraph.from_contract(
            cls.contract["connections"],
            cls.placements,
        )

    def test_every_physical_component_pin_has_exactly_one_connection(self) -> None:
        expected = {
            (item.reference, logical)
            for item in self.placements
            for logical, _physical, _position, _definition in item.pads()
        }
        actual = {
            endpoint
            for connection in self.graph.connections
            for endpoint in connection.endpoints
        }
        self.assertEqual(actual, expected)

    def test_every_component_resolves_every_semantic_pin_attachment(self) -> None:
        for reference, entry in self.contract["components"].items():
            component = for_netlist_entry(reference, entry)
            with self.subTest(reference=reference):
                self.assertEqual(
                    set(component.attachments(self.graph)),
                    set(component.get_pins()),
                )

    def test_component_resolves_its_semantic_pin_attachments(self) -> None:
        hall = HallSensor("HS1")
        self.assertEqual(
            hall.attachments(self.graph),
            {
                HallSensorPin.SUPPLY: Net.THREE_VOLTS_THREE,
                HallSensorPin.ACTIVE_LOW_OUTPUT: "SQ_A1",
                HallSensorPin.GROUND: Net.GROUND,
            },
        )

    def test_one_hall_sensor_exposes_power_ground_and_square_output(self) -> None:
        connections = self.graph.for_component("HS1")
        by_endpoint = {
            endpoint: connection.name
            for connection in connections
            for endpoint in connection.endpoints
            if endpoint[0] == "HS1"
        }
        self.assertEqual(
            by_endpoint,
            {
                ("HS1", HallSensorPin.SUPPLY): Net.THREE_VOLTS_THREE,
                ("HS1", HallSensorPin.GROUND): Net.GROUND,
                ("HS1", HallSensorPin.ACTIVE_LOW_OUTPUT): "SQ_A1",
            },
        )

    def test_net_names_are_unique_and_stable(self) -> None:
        self.assertEqual(tuple(sorted(self.graph.names)), self.graph.names)
        self.assertEqual(len(self.graph.names), len(set(self.graph.names)))

    def test_duplicate_final_names_are_rejected(self) -> None:
        hall = HallSensor("HS1")
        for first_name, second_name in (("SUPPLY", "SUPPLY"), ("N$2", None)):
            with self.subTest(first_name=first_name, second_name=second_name):
                builder = connectivity.CircuitBuilder()
                builder.connect(hall.pin(HallSensorPin.SUPPLY), name=first_name)
                builder.connect(hall.pin(HallSensorPin.GROUND), name=second_name)
                with self.assertRaisesRegex(ValueError, "duplicate connection name"):
                    builder.build()

    def test_unique_named_groups_remain_separate(self) -> None:
        hall = HallSensor("HS1")
        graph = (
            connectivity.CircuitBuilder()
            .connect(hall.pin(HallSensorPin.SUPPLY), name="SUPPLY")
            .connect(hall.pin(HallSensorPin.GROUND), name="GROUND")
            .build()
        )
        self.assertEqual(graph.names, ("GROUND", "SUPPLY"))
        self.assertEqual(graph.peers(hall.endpoint(HallSensorPin.SUPPLY)), ())

    def test_serialized_duplicate_names_are_rejected(self) -> None:
        connections = copy.deepcopy(self.contract["connections"])
        connections[1]["name"] = connections[0]["name"]
        with self.assertRaisesRegex(ValueError, "duplicate connection name"):
            connectivity.ConnectionGraph.from_contract(connections, self.placements)

    def test_named_nets_are_the_projection_of_authoritative_connections(self) -> None:
        expected = {
            connection["name"]: connection["pads"]
            for connection in self.contract["connections"]
            if connection["name"] is not None
        }
        self.assertEqual(self.contract["nets"], expected)

    def test_duplicate_endpoint_is_rejected(self) -> None:
        connections = copy.deepcopy(self.contract["connections"])
        connections[1]["pads"].append(connections[0]["pads"][0])
        with self.assertRaisesRegex(ValueError, "belongs to multiple nets"):
            connectivity.ConnectionGraph.from_contract(
                connections,
                self.placements,
            )

    def test_missing_endpoint_is_rejected(self) -> None:
        connections = copy.deepcopy(self.contract["connections"])
        connections[0]["pads"].pop()
        with self.assertRaisesRegex(ValueError, "lack connections"):
            connectivity.ConnectionGraph.from_contract(
                connections,
                self.placements,
            )


if __name__ == "__main__":
    unittest.main()
