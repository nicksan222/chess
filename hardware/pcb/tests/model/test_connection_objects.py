"""Connection definitions own invariants before they enter a graph or adapter."""

import unittest

from board import definition
from components.hall_sensor import HallSensor, HallSensorPin
from domain.component import Endpoint
from domain.connection_contract import ConnectionContract
from domain.connectivity import CircuitBuilder, Connection, ConnectionGraph


class ConnectionObjectsTest(unittest.TestCase):
    def setUp(self):
        self.first = HallSensor("HS1").pin(HallSensorPin.SUPPLY)
        self.second = HallSensor("HS2").pin(HallSensorPin.SUPPLY)

    def test_definition_keeps_bound_semantic_pins_and_graph_identity(self):
        connection = Connection.from_pins("SUPPLY", self.first, self.second)
        graph = CircuitBuilder().add(connection).build()
        self.assertIs(graph.named("SUPPLY"), connection)
        self.assertIs(graph.connection_for(self.first.endpoint), connection)
        self.assertIsInstance(connection.endpoints[0], Endpoint)
        self.assertIs(connection.endpoints[0].pin, HallSensorPin.SUPPLY)
        self.assertTrue(self.first.is_attached_to(self.second, graph))

    def test_empty_duplicate_and_multi_pin_no_connect_definitions_are_rejected(self):
        cases = (
            lambda: Connection("EMPTY", ()),
            lambda: Connection.from_pins("TWICE", self.first, self.first),
            lambda: Connection.from_pins(
                "NC", self.first, self.second, no_connect=True
            ),
        )
        for make_connection in cases:
            with (
                self.subTest(make_connection=make_connection),
                self.assertRaises(ValueError),
            ):
                make_connection()

    def test_duplicate_in_one_builder_call_does_not_claim_the_pin(self):
        builder = CircuitBuilder()
        with self.assertRaises(ValueError):
            builder.connect(self.first, self.first, name="INVALID")
        builder.connect(self.first, name="VALID")
        self.assertEqual(builder.build().names, ("VALID",))

    def test_failed_attachment_leaves_other_pins_available(self):
        builder = CircuitBuilder().connect(self.first, name="FIRST")
        with self.assertRaisesRegex(ValueError, "already attached"):
            builder.add(Connection.from_pins("INVALID", self.first, self.second))
        builder.connect(self.second, name="SECOND")
        self.assertEqual(builder.build().names, ("FIRST", "SECOND"))

    def test_no_connect_is_an_explicit_single_pin_definition(self):
        connection = Connection.from_pins("NC", self.first, no_connect=True)
        graph = CircuitBuilder().add(connection).build()
        self.assertTrue(graph.named("NC").no_connect)
        self.assertEqual(self.first.peers(graph), ())

    def test_missing_named_connection_has_context(self):
        with self.assertRaisesRegex(KeyError, "no connection named 'MISSING'"):
            ConnectionGraph(()).named("MISSING")

    def test_contract_object_preserves_typed_graph_and_physical_no_connect_names(self):
        from domain import sources

        design = definition.load()
        contract = ConnectionContract(
            design.placements,
            {reference: item.model for reference, item in design.components.items()},
        )
        graph = contract.build(sources.netlist()["connections"])
        self.assertEqual(graph.connections, design.connections.connections)
        for connection in graph.connections:
            for endpoint in connection.endpoints:
                self.assertIsInstance(endpoint, Endpoint)
            if connection.no_connect:
                reference, logical = connection.endpoints[0]
                physical = next(
                    number
                    for pin, number, *_ in design.component(reference).placement.pads()
                    if pin == logical
                )
                self.assertEqual(
                    connection.name, f"unconnected-({reference}-Pad{physical})"
                )

    def test_contract_rejects_wrong_json_types_before_building_connections(self):
        entries = (
            {"pads": "HS1:1"},
            {"pads": [["HS1", 1]]},
            {"pads": [["HS1", "1"]], "name": 12},
            {"pads": [["HS1", "1"]], "no_connect": "false"},
        )
        contract = ConnectionContract(())
        for entry in entries:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                contract.build([entry])

    def test_component_model_accessor_checks_product_before_exposing_pins(self):
        from components.tca9554 import Tca9554

        component = definition.load().component("HS1")
        self.assertIs(component.model_as(HallSensor), component.model)
        with self.assertRaisesRegex(ValueError, "HS1: expected Tca9554"):
            component.model_as(Tca9554)

    def test_from_contract_preserves_graph_subclass(self):
        class SpecializedGraph(ConnectionGraph):
            pass

        self.assertIsInstance(SpecializedGraph.from_contract([], []), SpecializedGraph)


if __name__ == "__main__":
    unittest.main()
