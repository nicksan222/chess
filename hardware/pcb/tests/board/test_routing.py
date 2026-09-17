"""Focused native-board checks for deterministic routing boundaries."""

import unittest
from itertools import pairwise

import pcbnew

from pcb.definition import rules
from pcb.definition.routing import paths


class RoutingTest(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(8)
        self.layers = (pcbnew.In4_Cu, pcbnew.In5_Cu)
        self.net = pcbnew.NETINFO_ITEM(self.board, "SIGNAL", 1)
        self.foreign = pcbnew.NETINFO_ITEM(self.board, "FOREIGN", 2)
        self.board.Add(self.net)
        self.board.Add(self.foreign)
        corners = ((0, 0), (30, 0), (30, 30), (0, 30), (0, 0))
        for start, end in pairwise(corners):
            edge = pcbnew.PCB_SHAPE(self.board)
            edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(self.point(*start))
            edge.SetEnd(self.point(*end))
            edge.SetLayer(pcbnew.Edge_Cuts)
            edge.SetWidth(0)
            self.board.Add(edge)

    @staticmethod
    def point(x: float, y: float) -> pcbnew.VECTOR2I:
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def route(
        self,
        start: tuple[float, float] = (10, 10),
        end: tuple[float, float] = (12, 10),
        **options,
    ) -> paths.Route:
        return paths.find_route(
            self.board,
            self.net,
            self.point(*start),
            self.point(*end),
            layers=self.layers,
            **options,
        )

    def add_pad(
        self, *, through_hole: bool = False, same_net: bool = False
    ) -> pcbnew.PAD:
        footprint = pcbnew.FOOTPRINT(self.board)
        self.board.Add(footprint)
        pad = pcbnew.PAD(footprint)
        pad.SetPosition(self.point(10, 10))
        pad.SetSize(self.point(0.5, 0.5))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        if through_hole:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetDrillSize(self.point(0.3, 0.3))
            pad.SetLayerSet(pad.PTHMask())
        else:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pad.SMDMask())
        pad.SetNet(self.net if same_net else self.foreign)
        footprint.Add(pad)
        return pad

    def blocked(
        self, extra: frozenset[tuple[int, int]] = frozenset()
    ) -> tuple[dict[int, set[tuple[int, int]]], set[tuple[int, int]]]:
        return paths.blocked_cells(
            self.board,
            self.net.GetNetCode(),
            (0, 0, 120, 120),
            self.layers,
            extra,
        )

    def test_exact_and_snapped_endpoints_must_stay_inside_bounds(self):
        with self.assertRaisesRegex(ValueError, "start endpoint is outside"):
            self.route(start=(9.99, 15), routing_bounds_mm=(10, 10, 20, 20))
        with self.assertRaisesRegex(ValueError, "snapped start endpoint is outside"):
            self.route(
                start=(10.1, 15),
                end=(11, 15),
                routing_bounds_mm=(10.05, 10, 20, 20),
            )

    def test_start_and_end_layer_indices_are_validated(self):
        for option in ("preferred_layer_index", "required_end_layer_index"):
            with (
                self.subTest(option=option),
                self.assertRaisesRegex(ValueError, "layer index"),
            ):
                self.route(**{option: len(self.layers)})

        route = self.route(
            preferred_layer_index=0,
            required_end_layer_index=1,
        )
        self.assertEqual(route.points[0][2], 0)
        self.assertEqual(route.points[-1][2], 1)

    def test_pad_clearance_and_via_keepouts_are_distinct(self):
        outer_pad = self.add_pad()
        blocked, via_forbidden = self.blocked(frozenset({(60, 60)}))
        self.assertTrue(all((40, 40) not in cells for cells in blocked.values()))
        self.assertIn((40, 40), via_forbidden)
        self.assertIn((60, 60), via_forbidden)
        self.assertNotIn((45, 40), via_forbidden)

        self.board.Remove(outer_pad.GetParentFootprint())
        self.add_pad(through_hole=True, same_net=True)
        _, via_forbidden = self.blocked()
        self.assertIn((40, 40), via_forbidden)

    def test_route_and_exact_stubs_stay_inside_bank_corridor(self):
        start, end = (10, 15.01), (20, 15.01)
        corridor = (10.0, 10.0, 20.0, 20.0)
        route = self.route(start, end, routing_bounds_mm=corridor)
        paths.apply_route(
            self.board,
            self.net,
            self.point(*start),
            self.point(*end),
            route,
        )
        self.assertGreater(len(tuple(self.board.GetTracks())), 0)
        for track in self.board.GetTracks():
            if isinstance(track, pcbnew.PCB_VIA):
                continue
            for point in (track.GetStart(), track.GetEnd()):
                self.assertTrue(10 <= pcbnew.ToMM(point.x) <= 20)
                self.assertTrue(10 <= pcbnew.ToMM(point.y) <= 20)

    def test_apply_route_omits_zero_length_stubs_and_uses_native_dimensions(self):
        route = paths.Route(
            (
                (40, 40, 0),
                (44, 40, 0),
                (44, 40, 1),
                (48, 40, 1),
            ),
            self.layers,
        )
        paths.apply_route(
            self.board,
            self.net,
            self.point(10, 10),
            self.point(12, 10),
            route,
        )
        items = tuple(self.board.GetTracks())
        vias = tuple(item for item in items if isinstance(item, pcbnew.PCB_VIA))
        tracks = tuple(item for item in items if not isinstance(item, pcbnew.PCB_VIA))
        self.assertEqual(len(tracks), 2)
        self.assertEqual(len(vias), 1)
        self.assertEqual({track.GetLayer() for track in tracks}, set(self.layers))
        self.assertTrue(
            all(
                track.GetWidth() == pcbnew.FromMM(rules.TRACE_WIDTH_MM)
                for track in tracks
            )
        )
        self.assertEqual(vias[0].GetWidth(), pcbnew.FromMM(rules.VIA_PAD_MM))
        self.assertEqual(vias[0].GetDrillValue(), pcbnew.FromMM(rules.VIA_DRILL_MM))

    def test_equal_cost_routes_use_stable_neighbour_order(self):
        expected = ((40, 40, 0), (48, 40, 0), (48, 48, 0))
        routes = {
            self.route(
                start=(10, 10),
                end=(12, 12),
                preferred_layer_index=0,
                allow_vias=False,
            ).points
            for _ in range(3)
        }
        self.assertEqual(routes, {expected})


if __name__ == "__main__":
    unittest.main()
