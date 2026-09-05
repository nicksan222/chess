"""Subsystem objects share copper state but retain their distinct routing schedules."""

import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

try:
    from kicad.api import pcbnew
except ModuleNotFoundError:
    pcbnew = None

if pcbnew is not None:
    from board import definition
    from board.wiring import common
    from board.wiring.buttons import ButtonWiring
    from board.wiring.context import WiringContext, WiringStage
    from board.wiring.controls import ControlSignalWiring, InternalBusWiring
    from board.wiring.led import LedChainWiring
    from board.wiring.nets import Net
    from board.wiring.power import InputPowerWiring, PowerFanoutWiring
    from board.wiring.router import ChessBoardRouter
    from board.wiring.sensors import HallSensorWiring
    from board.wiring.signal_tree import SignalTreeWiring
    from domain.connectivity import Connection, ConnectionGraph
    from kicad.board import KiCadBoard


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class WiringObjectsTest(unittest.TestCase):
    def setUp(self):
        self.design = definition.load()
        self.layout = KiCadBoard(self.design)
        self.context = WiringContext.from_layout(self.layout)

    def test_context_borrows_exact_layout_objects_and_is_not_rebindable(self):
        for name, expected in (
            ("board", self.layout.native),
            ("nets", self.layout.nets),
            ("pads", self.layout.pads),
            ("connections", self.design.connections),
            ("design", self.design),
        ):
            self.assertIs(getattr(self.context, name), expected)
        with self.assertRaises(FrozenInstanceError):
            self.context.board = pcbnew.BOARD()
        self.assertIs(
            self.context.connection(Net.I2C_SDA),
            self.design.connections.named(Net.I2C_SDA),
        )

    def test_base_requires_a_real_routing_policy(self):
        for abstract in (WiringStage, SignalTreeWiring):
            with self.subTest(abstract=abstract), self.assertRaises(TypeError):
                abstract(self.context)

    def test_pipeline_composes_objects_in_dependency_order(self):
        router = ChessBoardRouter(self.layout)
        before = router.before_sensor_reservation
        after = router.after_sensor_reservation
        self.assertEqual(
            tuple(type(stage) for stage in before),
            (PowerFanoutWiring, LedChainWiring, ControlSignalWiring),
        )
        self.assertEqual(
            tuple(type(stage) for stage in after),
            (
                ButtonWiring,
                InternalBusWiring,
                HallSensorWiring,
                LedChainWiring,
                InputPowerWiring,
            ),
        )
        self.assertFalse(before[1].obstructed_only)
        self.assertTrue(after[3].obstructed_only)
        self.assertIs(after[2], router.sensors)
        for stage in (*before, *after):
            self.assertIs(stage.context, router.context)
            self.assertIsInstance(stage, WiringStage)
        events = []
        for index, stage in enumerate((*before, *after)):
            patcher = patch.object(
                stage, "route", side_effect=lambda i=index: events.append(i)
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        with (
            patch.object(
                router.sensors, "reserve", side_effect=lambda: events.append("reserve")
            ),
            patch.object(
                common,
                "prune_unused_signal_vias",
                side_effect=lambda board: events.append("prune"),
            ),
        ):
            router.route()
        self.assertEqual(events, [0, 1, 2, "reserve", 3, 4, 5, 6, 7, "prune"])

    def record_tree(self, wiring_type, names):
        # Contract order is deliberately not host-first. Control escapes retain
        # that order; bus escapes follow the sorted, host-rooted tree order.
        graph = ConnectionGraph(
            Connection(name, (("U5", str(index)), ("J1", str(index))))
            for index, name in enumerate(names, 1)
        )
        context = WiringContext(self.layout.native, self.layout.nets, {}, graph)
        wiring = wiring_type(context)
        events = []

        def escape(name, endpoint, *, add_via):
            self.assertTrue(add_via)
            events.append(("escape", name, endpoint[0]))
            return pcbnew.VECTOR2I(0 if endpoint[0] == "J1" else 10, 0)

        def connect(net, start, end, **options):
            self.assertEqual((start.x, end.x), (0, 10))
            events.append(("route", net.GetNetname(), options))

        with (
            patch.object(wiring, "escape", side_effect=escape),
            patch.object(wiring, "connect", side_effect=connect),
        ):
            wiring.route()
        return events

    def test_control_trees_reserve_all_endpoints_before_first_path(self):
        names = (Net.SPI_DATA, Net.LED_CLOCK)
        events = self.record_tree(ControlSignalWiring, names)
        self.assertEqual([event[0] for event in events], ["escape"] * 4 + ["route"] * 2)
        self.assertEqual([event[2] for event in events[:4]], ["U5", "J1"] * 2)
        self.assertEqual([event[1] for event in events[4:]], sorted(names))
        self.assertTrue(all(event[2] == {"allow_vias": True} for event in events[4:]))

    def test_internal_buses_reserve_each_tree_and_use_distinct_preferred_layers(self):
        events = self.record_tree(InternalBusWiring, (Net.I2C_SDA, Net.I2C_SCL))
        self.assertEqual(
            [event[0] for event in events], ["escape", "escape", "route"] * 2
        )
        self.assertEqual([events[index][2] for index in (0, 1, 3, 4)], ["J1", "U5"] * 2)
        for layer_index, event in enumerate((events[2], events[5])):
            self.assertEqual(
                event[2],
                {
                    "preferred_layer_index": layer_index,
                    "allow_vias": True,
                    "layers": common.INTERNAL_SIGNAL_LAYERS,
                },
            )

    def test_shared_tree_reports_endpoint_context_for_control_failures(self):
        wiring = ControlSignalWiring(self.context)
        connection = self.context.connection(Net.SPI_DATA)
        nodes = wiring.nodes(connection)
        points = {node: pcbnew.VECTOR2I(index, 0) for index, node in enumerate(nodes)}
        with patch.object(wiring, "connect", side_effect=RuntimeError("blocked")):
            with self.assertRaisesRegex(RuntimeError, "blocked: .* ->"):
                wiring.route_tree(connection, nodes, points, label_errors=True)
            with self.assertRaisesRegex(RuntimeError, "^blocked$"):
                wiring.route_tree(connection, nodes, points)

    def test_hall_object_retains_reservations_and_bank_bounds(self):
        for component in self.design.components.values():
            self.layout.attach(component)
        wiring = HallSensorWiring(self.context)
        pending = wiring.reserve()
        self.assertIs(pending, wiring.pending)
        self.assertEqual(len(pending), 64)
        with patch.object(wiring, "connect") as connect:
            wiring.route()
        self.assertEqual(connect.call_count, 64)
        for reservation, call in zip(pending, connect.call_args_list, strict=True):
            self.assertEqual(
                call.args, (reservation.net, reservation.start, reservation.end)
            )
            self.assertEqual(call.kwargs["routing_bounds_mm"], reservation.bounds_mm)
            self.assertEqual(call.kwargs["layers"], common.SENSOR_ROUTING_LAYERS)
            self.assertTrue(call.kwargs["diagonals"])

    def test_context_and_hall_fail_clearly_without_required_domain_state(self):
        context = WiringContext(self.layout.native, {}, {})
        with self.assertRaisesRegex(ValueError, "requires a connection graph"):
            context.connection("missing")
        with self.assertRaisesRegex(ValueError, "require a board design"):
            HallSensorWiring(context).reserve()


if __name__ == "__main__":
    unittest.main()
