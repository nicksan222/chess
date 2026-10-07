"""Routing declarations must preserve pin ownership, width and local bounds."""

from __future__ import annotations

import importlib.util
import unittest
from dataclasses import replace
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

from pcb.harness import BoardComponent, Circuit, Net, Placement
from pcb.harness.base.pcbnew.render.board_test import Nets, Pin, sample_board

if TYPE_CHECKING:
    from .engine import RoutingContext


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class EngineTest(unittest.TestCase):
    def fixture(self, *, duplicate_receiver_pad: bool = False) -> RoutingContext:
        from pcb.harness.base.pcbnew.render.board import render_board

        from .engine import context
        from .settings import RoutingSettings

        circuit = sample_board()
        part = cast(BoardComponent[Pin], circuit.components()[0])
        definition = part.definition
        if duplicate_receiver_pad:
            from ..land_pattern import LandPattern
            from ..pad import Pad
            from ..point import Point

            pattern = definition.land_pattern
            assert pattern is not None
            definition = replace(
                definition,
                product=replace(
                    definition.product, part_number="Duplicate-pad receiver"
                ),
                land_pattern=LandPattern(
                    Pin,
                    (Pad(Pin.A, Point(-1, 1), 1, 1, number="1b"), *pattern.pads),
                ),
            )
        circuit.place(
            BoardComponent,
            reference="U2",
            definition=definition,
            placement=Placement(5, 0),
            purpose="second receiver",
            pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
        )
        return context(
            cast(Circuit[Net], circuit),
            render_board(circuit),
            RoutingSettings(),
            "U1",
            frozenset(),
            frozenset(),
        )

    def test_net_route_honours_width_and_local_area(self) -> None:
        import pcbnew

        from .definition import NetRoute
        from .engine import route_plan

        ctx = self.fixture()
        route_plan(ctx, (NetRoute(Nets.POWER, width_mm=0.4, area=(-9, -4, 9, 4)),))
        traces = [
            trace
            for trace in ctx.board.GetTracks()
            if not isinstance(trace, pcbnew.PCB_VIA)
        ]
        self.assertGreater(len(traces), 0)
        for trace in traces:
            self.assertEqual(trace.GetWidth(), pcbnew.FromMM(0.4))
            self.assertEqual(trace.GetNetname(), Nets.POWER.label)
            for point in (trace.GetStart(), trace.GetEnd()):
                x, y = pcbnew.ToMM(point.x) - 10, 5 - pcbnew.ToMM(point.y)
                self.assertTrue(-9 <= x <= 9 and -4 <= y <= 4)

    def test_explicit_path_cannot_rewire_a_component_pin(self) -> None:
        from pcb.harness import CopperPath, Endpoint

        from .engine import apply_paths

        ctx = self.fixture()
        wrong = CopperPath(Nets.POWER, (Endpoint("U1", "1"), Endpoint("U2", "2")))
        with self.assertRaisesRegex(ValueError, "pin's net"):
            apply_paths(ctx, (wrong,))
        self.assertEqual(list(ctx.board.GetTracks()), [])
        self.assertEqual(
            ctx.pads_by_endpoint[Endpoint("U2", "2")].GetNetname(), Nets.GROUND.label
        )

    def test_foreign_net_enum_is_rejected_before_routing(self) -> None:
        from .definition import NetRoute, validate_routes

        class OtherNet(Net):
            POWER = "+3V3"

        with self.assertRaisesRegex(ValueError, "circuit's net enum"):
            validate_routes(Nets, (NetRoute(OtherNet.POWER),))

    def test_connector_route_prefers_numbered_pin_over_duplicate_pad(self) -> None:
        import pcbnew

        from pcb.harness import CopperLayer, NetRoute, PinLaunch

        from .engine import find_route, footprint
        from .launch import route_launched_nets

        ctx = self.fixture(duplicate_receiver_pad=True)
        receiver = footprint(ctx.board, "U2")
        primary = next(pad for pad in receiver.Pads() if pad.GetNumber() == "1")
        with patch(f"{__package__}.launch.find_route", wraps=find_route) as router:
            route_launched_nets(
                ctx,
                (NetRoute(Nets.POWER, launch=PinLaunch("U1", (CopperLayer.BOTTOM,))),),
            )
        endpoint = cast(pcbnew.VECTOR2I, router.call_args_list[-1].args[3])
        self.assertEqual(
            (endpoint.x, endpoint.y), (primary.GetPosition().x, primary.GetPosition().y)
        )
        self.assertGreater(len(list(ctx.board.GetTracks())), 0)

    def test_duplicate_connector_pads_route_around_foreign_copper(self) -> None:
        import pcbnew

        from pcb.harness import CopperLayer, NetRoute, PinLaunch

        from . import copper
        from .engine import footprint
        from .launch import route_launched_nets

        ctx = self.fixture(duplicate_receiver_pad=True)
        receiver = footprint(ctx.board, "U2")
        pads = {pad.GetNumber(): pad for pad in receiver.Pads()}
        pads["1b"].SetPosition(
            pcbnew.VECTOR2I(pads["1"].GetPosition().x, pcbnew.FromMM(2))
        )
        # The old unchecked straight join would cross this foreign trace.
        copper.add_trace(
            ctx.board,
            ctx.nets_by_name[Nets.GROUND.label],
            pcbnew.VECTOR2I(pcbnew.FromMM(12), pcbnew.FromMM(3.5)),
            pcbnew.VECTOR2I(pcbnew.FromMM(16), pcbnew.FromMM(3.5)),
        )
        route_launched_nets(
            ctx,
            (NetRoute(Nets.POWER, launch=PinLaunch("U1", (CopperLayer.BOTTOM,))),),
        )
        for track in ctx.board.GetTracks():
            if (
                isinstance(track, pcbnew.PCB_VIA)
                or track.GetNetname() != Nets.POWER.label
            ):
                continue
            if track.GetLayer() == pcbnew.F_Cu:
                start, end = track.GetStart(), track.GetEnd()
                self.assertFalse(
                    start.x == end.x == pads["1"].GetPosition().x
                    and min(start.y, end.y) < pcbnew.FromMM(3.5) < max(start.y, end.y)
                )

    def test_later_reserved_escapes_exist_before_connector_routing(self) -> None:
        import pcbnew

        from pcb.harness import CopperLayer, NetRoute, PinLaunch

        from .engine import route_plan

        ctx = self.fixture()
        with (
            patch(f"{__package__}.launch.route_launched_nets") as connector,
            patch(f"{__package__}.engine.route_nets"),
        ):

            def check_reserved(*_args: object) -> None:
                self.assertTrue(
                    any(
                        isinstance(track, pcbnew.PCB_VIA)
                        and track.GetNetname() == Nets.POWER.label
                        for track in ctx.board.GetTracks()
                    )
                )

            connector.side_effect = check_reserved
            route_plan(
                ctx,
                (
                    NetRoute(
                        Nets.GROUND,
                        priority=1,
                        launch=PinLaunch("U1", (CopperLayer.BOTTOM,)),
                    ),
                    NetRoute(Nets.POWER, priority=2, reserve_group=True),
                ),
            )
            connector.assert_called_once()
