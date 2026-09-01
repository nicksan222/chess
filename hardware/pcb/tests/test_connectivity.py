"""Electrical contracts become one validated, navigable connection graph."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from components.catalog import for_netlist_entry
from components.hall_sensor import HallSensor, HallSensorPin
from core import connectivity, placement, sources
from core.nets import Net


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
