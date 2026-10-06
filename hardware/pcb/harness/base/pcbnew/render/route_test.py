"""Check explicit traces and vias become native KiCad route objects.

The tests inspect layer, size, and net metadata written by the adapter. They
deliberately do not check pad contact, obstacle clearance, route continuity,
or any KiCad DRC result.
"""

import importlib.util
import unittest

from pcb.harness import Net
from pcb.harness.base.pcbnew.outline import BoardOutline
from pcb.harness.base.pcbnew.point import Point
from pcb.harness.base.pcbnew.route import CopperLayer, Trace, Via


class Nets(Net):
    """Typed copper net used in route conversion checks."""

    POWER = "+3V3"


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderRouteTest(unittest.TestCase):
    """Check native track/via metadata without running DRC."""

    def test_trace_layer_width_and_net_are_preserved(self) -> None:
        """A trace retains its copper face, width, and assigned native net."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.route import render_trace

        board = pcbnew.BOARD()
        net = pcbnew.NETINFO_ITEM(board, Nets.POWER.label, board.GetNetCount())
        board.Add(net)
        native = render_trace(
            board,
            Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.BOTTOM, 0.25),
            BoardOutline(20, 10),
            net,
        )
        # These fields check conversion of route choices; they do not prove endpoint connectivity.
        self.assertEqual(native.GetLayer(), pcbnew.B_Cu)
        self.assertEqual(native.GetWidth(), pcbnew.FromMM(0.25))
        self.assertEqual(native.GetNetname(), Nets.POWER.label)

    def test_via_has_declared_drill_and_copper_diameter(self) -> None:
        """A via keeps separate copper-diameter and drill-size declarations."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.route import render_via

        board = pcbnew.BOARD()
        net = pcbnew.NETINFO_ITEM(board, Nets.POWER.label, board.GetNetCount())
        board.Add(net)
        native = render_via(
            board, Via(Nets.POWER, Point(0, 0), 0.7, 0.3), BoardOutline(20, 10), net
        )
        # Outer width is copper diameter; drill value is the smaller hole diameter.
        self.assertEqual(native.GetWidth(pcbnew.F_Cu), pcbnew.FromMM(0.7))
        self.assertEqual(native.GetDrillValue(), pcbnew.FromMM(0.3))

    def test_top_trace_uses_front_copper(self) -> None:
        """The top enum must not silently render as back copper."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.route import render_trace

        board = pcbnew.BOARD()
        net = pcbnew.NETINFO_ITEM(board, Nets.POWER.label, board.GetNetCount())
        board.Add(net)
        native = render_trace(
            board,
            Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.TOP, 0.25),
            BoardOutline(20, 10),
            net,
        )
        self.assertEqual(native.GetLayer(), pcbnew.F_Cu)

    def test_route_rejects_native_net_from_another_logical_net(self) -> None:
        """A converter call cannot connect a typed route to an unrelated net."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.route import render_trace, render_via

        board = pcbnew.BOARD()
        wrong = pcbnew.NETINFO_ITEM(board, "GND", board.GetNetCount())
        board.Add(wrong)
        with self.assertRaisesRegex(ValueError, "net"):
            render_trace(
                board,
                Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.TOP, 0.25),
                BoardOutline(20, 10),
                wrong,
            )
        with self.assertRaisesRegex(ValueError, "net"):
            render_via(
                board,
                Via(Nets.POWER, Point(0, 0), 0.7, 0.3),
                BoardOutline(20, 10),
                wrong,
            )
