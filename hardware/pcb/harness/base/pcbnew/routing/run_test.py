"""Package copper follows real instances and obeys their existing pin maps."""

import importlib.util
import unittest
from dataclasses import replace
from typing import cast

from pcb.harness import (
    BoardComponent,
    Circuit,
    CopperPath,
    Endpoint,
    PackagePath,
    PackageRouting,
    Placement,
    Point,
    RouteStage,
    RoutingPlan,
    Side,
)
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RoutingPlanTest(unittest.TestCase):
    def fixture(self, side: Side = Side.TOP) -> Circuit[Nets]:
        sample = sample_board()
        part = cast(BoardComponent[Pin], sample.components()[0])
        definition = replace(
            part.definition,
            routing=PackageRouting(
                paths=(
                    PackagePath(Pin.A, (Point(-1, 0), Point(-3, 0)), 0.31, via=True),
                ),
                ports=(("signal", Point(-3, 0)),),
            ),
        )
        circuit = Circuit(Nets, outline=sample.outline)
        for reference, placement in (
            ("First", Placement(-4, 0)),
            ("Second", Placement(4, 0, 90, side)),
        ):
            circuit.place(
                BoardComponent,
                reference=reference,
                definition=definition,
                placement=placement,
                purpose="independent package escape",
                pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
            )
        return circuit

    def test_package_copper_follows_each_instances_rotation(self) -> None:
        from .run import route
        from .settings import RoutingSettings

        circuit = self.fixture()
        route(circuit, RoutingPlan("First", (), (), ()), RoutingSettings())
        self.assertEqual(len(circuit.traces()), 2)
        self.assertEqual(len(circuit.vias()), 2)
        first, second = (
            cast(BoardComponent[Pin], part) for part in circuit.components()
        )
        self.assertEqual(first.port("signal"), Point(-7, 0))
        self.assertAlmostEqual(second.port("signal").x_mm, 4)
        self.assertAlmostEqual(second.port("signal").y_mm, -3)
        endpoints = {
            (round(trace.end.x_mm, 6), round(trace.end.y_mm, 6))
            for trace in circuit.traces()
        }
        self.assertEqual(endpoints, {(-7, 0), (4, -3)})
        self.assertTrue(all(trace.net is Nets.POWER for trace in circuit.traces()))

    def test_invalid_wiring_leaves_circuit_copper_untouched(self) -> None:
        from .run import route
        from .settings import RoutingSettings

        circuit = self.fixture()
        invalid = CopperPath(
            Nets.POWER, (Endpoint("First", "1"), Endpoint("Second", "2"))
        )
        with self.assertRaisesRegex(ValueError, "pin's net"):
            route(
                circuit,
                RoutingPlan("First", (), (), (RouteStage(paths=(invalid,)),)),
                RoutingSettings(),
            )
        self.assertEqual(circuit.traces(), ())
        self.assertEqual(circuit.vias(), ())

    def test_package_stubs_start_on_native_pads_on_either_board_face(self) -> None:
        import pcbnew

        from ..render.board import render_board
        from .run import route
        from .settings import RoutingSettings

        for side in Side:
            with self.subTest(side=side):
                circuit = self.fixture(side)
                route(circuit, RoutingPlan("First", (), (), ()), RoutingSettings())
                native = render_board(circuit)
                footprint = native.FindFootprintByReference("Second")
                assert footprint is not None
                pad = next(pad for pad in footprint.Pads() if pad.GetNumber() == "1")
                starts = {
                    (track.GetStart().x, track.GetStart().y)
                    for track in native.GetTracks()
                    if not isinstance(track, pcbnew.PCB_VIA)
                }
                self.assertIn((pad.GetPosition().x, pad.GetPosition().y), starts)
