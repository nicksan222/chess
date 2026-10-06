"""Check conversion of declarative pad facts into native KiCad pads.

The cases cover the fields the adapter writes directly: number, position,
attribute, layer set, drill, and optional net. They do not establish that a
manufacturer's component lead, solder mask, or routed track will fit.
"""

import importlib.util
import unittest
from enum import StrEnum

from pcb.harness import Net
from pcb.harness.base.connections import NetConnection, NoConnect
from pcb.harness.base.pcbnew.outline import BoardOutline
from pcb.harness.base.pcbnew.pad import Pad, PadKind, PadShape
from pcb.harness.base.pcbnew.point import Point


class Pin(StrEnum):
    A = "1"


class Nets(Net):
    POWER = "+3V3"


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderPadTest(unittest.TestCase):
    """Verify pad properties in native objects, not fit to a manufactured part."""

    def test_surface_pad_receives_copper_net_and_number(self) -> None:
        """A surface pad keeps its number, net, SMD kind, and board offset."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.pad import render_pad

        board = pcbnew.BOARD()
        footprint = pcbnew.FOOTPRINT(board)
        network = pcbnew.NETINFO_ITEM(board, Nets.POWER.label, board.GetNetCount())
        board.Add(network)
        native = render_pad(
            footprint,
            Pad(Pin.A, Point(1, 0), 1, 0.8),
            NetConnection(Nets.POWER),
            BoardOutline(20, 10),
            network,
            Point(0, 0),
        )
        # Number and net preserve logical wiring; attribute and X position check physical conversion.
        self.assertEqual(native.GetNumber(), "1")
        self.assertEqual(native.GetNetname(), Nets.POWER.label)
        self.assertEqual(native.GetAttribute(), pcbnew.PAD_ATTRIB_SMD)
        self.assertEqual(native.GetPosition().x, pcbnew.FromMM(11))

    def test_through_hole_no_connect_has_drill_but_no_net(self) -> None:
        """A no-connect through-hole gets a drill but no native net."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.pad import render_pad

        board = pcbnew.BOARD()
        native = render_pad(
            pcbnew.FOOTPRINT(board),
            Pad(Pin.A, Point(0, 0), 1.5, 1.5, PadKind.THROUGH_HOLE, drill_mm=0.8),
            NoConnect("unused"),
            BoardOutline(20, 10),
            None,
            Point(0, 0),
        )
        # PTH attribute and drill describe its hole; net code zero confirms no net attached.
        self.assertEqual(native.GetAttribute(), pcbnew.PAD_ATTRIB_PTH)
        self.assertEqual(native.GetDrillSize().x, pcbnew.FromMM(0.8))
        self.assertEqual(native.GetNetCode(), 0)

    def test_connection_requires_matching_native_net(self) -> None:
        """A connected logical pin requires its matching native net object."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.pad import render_pad

        with self.assertRaisesRegex(ValueError, "match"):
            render_pad(
                pcbnew.FOOTPRINT(pcbnew.BOARD()),
                Pad(Pin.A, Point(0, 0), 1, 1),
                NetConnection(Nets.POWER),
                BoardOutline(20, 10),
                None,
                Point(0, 0),
            )

    def test_connection_rejects_native_net_with_another_label(self) -> None:
        """A pad cannot silently receive a real but incorrect KiCad net."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.pad import render_pad

        board = pcbnew.BOARD()
        wrong = pcbnew.NETINFO_ITEM(board, "GND", board.GetNetCount())
        board.Add(wrong)
        with self.assertRaisesRegex(ValueError, "match"):
            render_pad(
                pcbnew.FOOTPRINT(board),
                Pad(Pin.A, Point(0, 0), 1, 1),
                NetConnection(Nets.POWER),
                BoardOutline(20, 10),
                wrong,
                Point(0, 0),
            )

    def test_each_declared_pad_shape_maps_to_its_native_shape(self) -> None:
        """Rectangle, circle and oval remain distinct after KiCad conversion."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.pad import render_pad

        expected = (
            (PadShape.RECTANGLE, pcbnew.PAD_SHAPE_RECT),
            (PadShape.CIRCLE, pcbnew.PAD_SHAPE_CIRCLE),
            (PadShape.OVAL, pcbnew.PAD_SHAPE_OVAL),
        )
        for shape, native_shape in expected:
            with self.subTest(shape=shape):
                board = pcbnew.BOARD()
                footprint = pcbnew.FOOTPRINT(board)
                native = render_pad(
                    footprint,
                    Pad(Pin.A, Point(0, 0), 1, 1, shape=shape),
                    NoConnect("test pad"),
                    BoardOutline(20, 10),
                    None,
                    Point(0, 0),
                )
                # KiCad resolves padstack layers through its board-owned footprint.
                board.Add(footprint)
                self.assertEqual(native.GetShape(), native_shape)
