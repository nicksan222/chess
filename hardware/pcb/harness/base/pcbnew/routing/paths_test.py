"""Exercise real copper obstacles in the reusable path search."""

import importlib.util
import unittest

from pcb.harness.base.pcbnew.render.board_test import sample_board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class PathsTest(unittest.TestCase):
    def test_signal_detours_around_foreign_copper(self) -> None:
        import pcbnew

        from pcb.harness.base.pcbnew.render.board import render_board

        from .copper import add_trace
        from .paths import apply_route, find_route, position

        board = render_board(sample_board())
        signal = board.FindNet("+3V3")
        ground = board.FindNet("GND")
        assert signal is not None and ground is not None
        # A vertical ground track blocks the direct horizontal signal path.
        start = pcbnew.VECTOR2I(pcbnew.FromMM(4), pcbnew.FromMM(5))
        end = pcbnew.VECTOR2I(pcbnew.FromMM(16), pcbnew.FromMM(5))
        add_trace(
            board,
            ground,
            pcbnew.VECTOR2I(pcbnew.FromMM(10), pcbnew.FromMM(3)),
            pcbnew.VECTOR2I(pcbnew.FromMM(10), pcbnew.FromMM(7)),
        )
        route = find_route(
            board, signal, start, end, layers=(pcbnew.F_Cu,), allow_vias=False
        )
        points = [position(node.cell) for node in route.points]
        self.assertTrue(
            any(
                pcbnew.ToMM(point.y) < 2.5 or pcbnew.ToMM(point.y) > 7.5
                for point in points
            )
        )
        apply_route(board, signal, start, end, route)
        self.assertGreater(len(list(board.GetTracks())), 2)
