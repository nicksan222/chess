"""Check that a rectangular declaration becomes native ``Edge.Cuts`` lines.

The test inspects the four generated ``PCB_SHAPE`` objects and their endpoints.
It proves the conversion has the expected count, layer, and extents; it does
not invoke KiCad's outline parser or manufacturing/DRC checks.
"""

import importlib.util
import unittest
from typing import cast

from pcb.harness.base.pcbnew.outline import BoardOutline


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderOutlineTest(unittest.TestCase):
    """Inspect native edge objects and their millimetre-derived corners."""

    def test_four_edge_cuts_segments_form_declared_rectangle(self) -> None:
        """Four ``Edge.Cuts`` segments meet at the declared rectangle corners."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.outline import render_outline

        board = pcbnew.BOARD()
        render_outline(board, BoardOutline(20, 10))
        edges = [cast(pcbnew.PCB_SHAPE, edge) for edge in board.GetDrawings()]
        # A four-sided closed perimeter must contain exactly four native segments.
        self.assertEqual(len(edges), 4)
        self.assertTrue(all(edge.GetLayer() == pcbnew.Edge_Cuts for edge in edges))
        corners = {
            (coordinate.x, coordinate.y)
            for edge in edges
            for coordinate in (edge.GetStart(), edge.GetEnd())
        }
        # The set proves both expected board extents and absence of a shifted origin.
        self.assertEqual(
            corners,
            {
                (0, 0),
                (pcbnew.FromMM(20), 0),
                (pcbnew.FromMM(20), pcbnew.FromMM(10)),
                (0, pcbnew.FromMM(10)),
            },
        )
