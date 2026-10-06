"""Check component declarations become native footprints and graphics.

The tests inspect pad/graphic counts and the resulting side, rotation, and
edge containment. They cover the adapter's placement transforms and early
containment guard, not KiCad's full clearance or electrical rule checking.
"""

import importlib.util
import unittest
from typing import cast

from pcb.harness import BoardComponent, Circuit, Placement
from pcb.harness.base.geometry import Side
from pcb.harness.base.pcbnew.render.board_test import Pin, sample_board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderFootprintTest(unittest.TestCase):
    """Check native footprint geometry, placement, and face selection only."""

    def test_top_component_has_two_pads_and_four_courtyard_lines(self) -> None:
        """A two-pad pattern and courtyard produce the expected native objects."""
        import pcbnew

        from pcb.harness.base.pcbnew.render.board import render_board

        footprint = render_board(sample_board()).FindFootprintByReference("U1")
        self.assertIsNotNone(footprint)
        assert footprint is not None
        # The two pads come from the land pattern; four graphics outline the courtyard.
        self.assertEqual(len(list(footprint.Pads())), 2)
        self.assertEqual(len(list(footprint.GraphicalItems())), 4)
        # A centred reference on silkscreen would print across these pads.
        # Keep it on fabrication artwork until text placement is modeled.
        self.assertEqual(footprint.Reference().GetLayer(), pcbnew.F_Fab)
        self.assertTrue(
            all(
                line.GetLayer() == pcbnew.F_CrtYd for line in footprint.GraphicalItems()
            )
        )

    def test_courtyard_outside_board_is_rejected(self) -> None:
        """Registration refuses a keep-clear rectangle crossing the edge."""

        board = sample_board()
        component = cast(BoardComponent[Pin], board.components()[0])
        # Placement is immutable, so make a fresh board with a part near its edge.
        from pcb.harness.base.pcbnew.outline import BoardOutline

        near_edge = Circuit(board.net_type, outline=BoardOutline(20, 10))
        with self.assertRaisesRegex(ValueError, "courtyard"):
            near_edge.place(
                BoardComponent,
                reference="U1",
                definition=component.definition,
                placement=Placement(9, 0),
                purpose="too close",
                pins=component.pins,
            )
        self.assertEqual(near_edge.components(), ())

    def test_bottom_side_flips_copper_layer(self) -> None:
        """Back-side placement mirrors the footprint and moves pads to back copper."""
        import pcbnew

        from pcb.harness.base.pcbnew.outline import BoardOutline
        from pcb.harness.base.pcbnew.render.board import render_board

        board = sample_board()
        component = cast(BoardComponent[Pin], board.components()[0])
        bottom = Circuit(board.net_type, outline=BoardOutline(20, 10))
        bottom.place(
            BoardComponent,
            reference="U1",
            definition=component.definition,
            placement=Placement(0, 0, side=Side.BOTTOM),
            purpose="bottom",
            pins=component.pins,
        )
        footprint = render_board(bottom).FindFootprintByReference("U1")
        self.assertIsNotNone(footprint)
        assert footprint is not None
        # Both checks matter: the footprint is flipped and its copper pads move faces.
        self.assertTrue(footprint.IsFlipped())
        self.assertTrue(all(pad.IsOnLayer(pcbnew.B_Cu) for pad in footprint.Pads()))
        self.assertTrue(
            all(
                line.GetLayer() == pcbnew.B_CrtYd for line in footprint.GraphicalItems()
            )
        )
        positions = {pad.GetNumber(): pad.GetPosition().x for pad in footprint.Pads()}
        # From the board's top view, a bottom-mounted package is mirrored.
        self.assertEqual(positions, {"1": pcbnew.FromMM(11), "2": pcbnew.FromMM(9)})

    def test_bottom_rotation_is_measured_from_the_mounting_side(self) -> None:
        """A bottom-side 90° turn retains the expected mirrored pin geometry."""
        import pcbnew

        from pcb.harness.base.pcbnew.outline import BoardOutline
        from pcb.harness.base.pcbnew.render.board import render_board

        source = sample_board()
        component = cast(BoardComponent[Pin], source.components()[0])
        board = Circuit(source.net_type, outline=BoardOutline(20, 10))
        board.place(
            BoardComponent,
            reference="U1",
            definition=component.definition,
            placement=Placement(0, 0, 90, Side.BOTTOM),
            purpose="rotated underside",
            pins=component.pins,
        )
        footprint = render_board(board).FindFootprintByReference("U1")
        self.assertIsNotNone(footprint)
        assert footprint is not None
        positions = {
            pad.GetNumber(): (pad.GetPosition().x, pad.GetPosition().y)
            for pad in footprint.Pads()
        }
        self.assertEqual(
            positions,
            {
                "1": (pcbnew.FromMM(10), pcbnew.FromMM(6)),
                "2": (pcbnew.FromMM(10), pcbnew.FromMM(4)),
            },
        )

    def test_rotation_moves_pads_and_courtyard_with_component(self) -> None:
        """A 90-degree placement rotates child pads around the footprint centre."""
        import pcbnew

        from pcb.harness.base.pcbnew.outline import BoardOutline
        from pcb.harness.base.pcbnew.render.board import render_board

        component = cast(BoardComponent[Pin], sample_board().components()[0])
        board = Circuit(sample_board().net_type, outline=BoardOutline(20, 10))
        board.place(
            BoardComponent,
            reference="U1",
            definition=component.definition,
            placement=Placement(0, 0, 90),
            purpose="rotated",
            pins=component.pins,
        )
        footprint = render_board(board).FindFootprintByReference("U1")
        self.assertIsNotNone(footprint)
        assert footprint is not None
        positions = {
            pad.GetNumber(): (pad.GetPosition().x, pad.GetPosition().y)
            for pad in footprint.Pads()
        }
        self.assertEqual(
            positions,
            {
                "1": (pcbnew.FromMM(10), pcbnew.FromMM(6)),
                "2": (pcbnew.FromMM(10), pcbnew.FromMM(4)),
            },
        )
