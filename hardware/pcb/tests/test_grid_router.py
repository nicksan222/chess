"""Synthetic native boards exercise grid clearance and exact-coordinate bounds."""

import unittest
from itertools import pairwise

try:
    from base.kicad.api import pcbnew
except ModuleNotFoundError:  # Host-only unit runs do not install KiCad.
    pcbnew = None

if pcbnew is not None:
    from base import rules
    from base.kicad import grid_router


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class GridRouterTest(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(8)
        self.layers = (pcbnew.In4_Cu, pcbnew.In5_Cu)
        self.net = pcbnew.NETINFO_ITEM(self.board, "SIGNAL", 1)
        self.foreign = pcbnew.NETINFO_ITEM(self.board, "FOREIGN", 2)
        self.board.Add(self.net)
        self.board.Add(self.foreign)
        outline = pcbnew.PCB_SHAPE(self.board)
        outline.SetShape(pcbnew.SHAPE_T_RECT)
        outline.SetStart(self.point(0, 0))
        outline.SetEnd(self.point(30, 30))
        outline.SetLayer(pcbnew.Edge_Cuts)
        outline.SetWidth(0)
        self.board.Add(outline)

    @staticmethod
    def point(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def pad(
        self, *, same_net=False, through_hole=False, non_plated=False, rectangle=False
    ):
        footprint = pcbnew.FOOTPRINT(self.board)
        self.board.Add(footprint)
        pad = pcbnew.PAD(footprint)
        pad.SetPosition(self.point(10, 10))
        pad.SetSize(self.point(0.5, 0.5))
        pad.SetShape(pcbnew.PAD_SHAPE_RECT if rectangle else pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(
            pcbnew.PAD_ATTRIB_NPTH
            if non_plated
            else pcbnew.PAD_ATTRIB_PTH
            if through_hole
            else pcbnew.PAD_ATTRIB_SMD
        )
        if through_hole or non_plated:
            pad.SetDrillSize(self.point(0.3, 0.3))
            pad.SetLayerSet(pad.PTHMask())
        else:
            pad.SetLayerSet(pad.SMDMask())
        if not non_plated:
            pad.SetNet(self.net if same_net else self.foreign)
        footprint.Add(pad)
        return pad

    def blocked(self, *, layers=None, extra=frozenset()):
        return grid_router._blocked(
            self.board,
            self.net.GetNetCode(),
            (0, 0, 120, 120),
            self.layers if layers is None else layers,
            extra,
        )

    def route(self, start=(10, 10), end=(12, 10), **options):
        return grid_router.find_route(
            self.board,
            self.net,
            self.point(*start),
            self.point(*end),
            layers=self.layers,
            **options,
        )

    def test_outer_pad_blocks_internal_through_via_but_not_internal_track(self):
        self.pad()
        blocked, forbidden = self.blocked()
        for cells in blocked.values():
            self.assertNotIn((40, 40), cells)
        self.assertIn((40, 40), forbidden)
        route = self.route(preferred_layer_index=0, required_end_layer_index=1)
        transitions = [a[:2] for a, b in pairwise(route.points) if a[2] != b[2]]
        self.assertTrue(transitions)
        self.assertTrue(all(cell not in forbidden for cell in transitions))

    def test_via_radius_is_distinct_from_track_radius_at_circular_pad(self):
        self.pad()
        blocked, forbidden = self.blocked(layers=(pcbnew.F_Cu, *self.layers))
        # At 0.75 mm centre distance: track clearance is 0.345 mm, via only 0.05 mm.
        self.assertNotIn((43, 40), blocked[pcbnew.F_Cu])
        self.assertIn((43, 40), forbidden)
        # At 1.25 mm distance the via has 0.55 mm edge-to-edge clearance.
        self.assertNotIn((45, 40), forbidden)

    def test_rectangular_outer_pad_also_blocks_internal_vias(self):
        self.pad(rectangle=True)
        _, forbidden = self.blocked()
        self.assertIn((40, 40), forbidden)
        self.assertIn((43, 40), forbidden)

    def test_foreign_tracks_and_vias_use_via_sized_clearance_on_unrouted_layers(self):
        for is_via in (False, True):
            with self.subTest(is_via=is_via):
                if is_via:
                    item = pcbnew.PCB_VIA(self.board)
                    item.SetPosition(self.point(10, 10))
                    item.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
                    item.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
                else:
                    item = pcbnew.PCB_TRACK(self.board)
                    item.SetStart(self.point(10, 8))
                    item.SetEnd(self.point(10, 12))
                    item.SetLayer(pcbnew.F_Cu)
                    item.SetWidth(pcbnew.FromMM(0.54))
                item.SetNet(self.foreign)
                self.board.Add(item)
                _, foreign_forbidden = self.blocked()
                item.SetNet(self.net)
                _, same_net_forbidden = self.blocked()
                self.board.Remove(item)
                # A 0.54 mm track at 1 mm centre distance leaves only
                # 1 - 0.27 - 0.45 = 0.28 mm clearance to a through-via.
                self.assertIn((44, 40), foreign_forbidden)
                self.assertNotIn((47, 40), foreign_forbidden)
                self.assertNotIn((40, 40), same_net_forbidden)

    def test_same_net_access_retains_hole_and_additional_keepouts(self):
        pad = self.pad(same_net=True)
        _, forbidden = self.blocked(extra=frozenset({(60, 60)}))
        self.assertNotIn((40, 40), forbidden)
        self.assertIn((60, 60), forbidden)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pad.PTHMask())
        blocked, forbidden = self.blocked()
        self.assertIn((40, 40), forbidden)
        self.assertTrue(all((40, 40) not in cells for cells in blocked.values()))

    def test_unplated_holes_block_tracks_and_vias(self):
        self.pad(non_plated=True)
        blocked, forbidden = self.blocked()
        self.assertIn((40, 40), forbidden)
        self.assertTrue(all((40, 40) in cells for cells in blocked.values()))

    def test_board_edge_allows_track_but_reserves_full_via_radius(self):
        for start, end in (
            ((0.75, 15), (2, 15)),
            ((29.25, 15), (28, 15)),
            ((15, 0.75), (15, 2)),
            ((15, 29.25), (15, 28)),
        ):
            with self.subTest(start=start):
                # A single-cell corridor admits a track centre at the edge,
                # but cannot accommodate the larger through-via annulus.
                corridor = (*start, *start)
                self.route(start, start, allow_vias=False, routing_bounds_mm=corridor)
                with self.assertRaisesRegex(RuntimeError, "no route"):
                    self.route(
                        start,
                        start,
                        preferred_layer_index=0,
                        required_end_layer_index=1,
                        routing_bounds_mm=corridor,
                    )
                route = self.route(
                    start, end, preferred_layer_index=0, required_end_layer_index=1
                )
                transitions = [a[:2] for a, b in pairwise(route.points) if a[2] != b[2]]
                self.assertTrue(transitions)
                for x, y in transitions:
                    edge_distance = min(x, y, 120 - x, 120 - y) * grid_router.GRID_MM
                    self.assertGreaterEqual(
                        edge_distance - rules.VIA_PAD_MM / 2, rules.POUR_TO_OUTLINE_MM
                    )

    def test_exact_outside_endpoints_are_rejected_even_when_snapped_inside(self):
        for outside in ((9.75, 15), (9.99, 15), (20.01, 15), (15, 9.99), (15, 20.01)):
            for label in ("start", "end"):
                with self.subTest(outside=outside, label=label):
                    endpoints = {
                        label: outside,
                        "end" if label == "start" else "start": (15, 15),
                    }
                    with self.assertRaisesRegex(
                        ValueError, f"{label} endpoint is outside"
                    ):
                        self.route(**endpoints, routing_bounds_mm=(10, 10, 20, 20))
        with self.assertRaisesRegex(ValueError, "start endpoint is outside"):
            self.route(start=(0.64, 15))

    def test_inverted_disjoint_and_raster_empty_bounds_are_rejected(self):
        for bounds in ((20, 10, 10, 20), (10, 20, 20, 10), (40, 40, 50, 50)):
            with (
                self.subTest(bounds=bounds),
                self.assertRaisesRegex(ValueError, "empty routing bounds"),
            ):
                self.route(routing_bounds_mm=bounds)
        with self.assertRaisesRegex(ValueError, "empty routing cell bounds"):
            self.route(
                start=(10.1, 15),
                end=(10.1, 15),
                routing_bounds_mm=(10.05, 10, 10.15, 20),
            )

    def test_snapped_endpoint_must_also_be_inside_bounds(self):
        with self.assertRaisesRegex(ValueError, "snapped start endpoint is outside"):
            self.route(
                start=(10.1, 15), end=(11, 15), routing_bounds_mm=(10.05, 10, 20, 20)
            )

    def test_boundary_adjacent_route_keeps_exact_stubs_in_corridor(self):
        start, end = (10, 15.01), (20, 15.01)
        route = self.route(start, end, routing_bounds_mm=(10, 10, 20, 20))
        grid_router.apply_route(
            self.board, self.net, self.point(*start), self.point(*end), route
        )
        self.assertGreater(len(self.board.GetTracks()), 0)
        for track in self.board.GetTracks():
            for point in (track.GetStart(), track.GetEnd()):
                self.assertTrue(10 <= pcbnew.ToMM(point.x) <= 20)
                self.assertTrue(10 <= pcbnew.ToMM(point.y) <= 20)


if __name__ == "__main__":
    unittest.main()
