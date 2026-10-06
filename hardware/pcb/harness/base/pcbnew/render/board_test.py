"""Check whole-board conversion, early rejection, and KiCad serialization.

The fixture uses only harness declarations. The tests then inspect the native
board's outline, nets, footprint, tracks, and vias, plus the checks that stop
rendering when required physical facts are absent or route copper crosses the
rectangular edge. Reloading the saved file proves basic serialization only;
these tests do not run KiCad DRC/ERC or prove manufacturing safety.
"""

import importlib.util
import tempfile
import unittest
from enum import StrEnum
from pathlib import Path
from typing import cast

from pcb.harness import (
    BoardComponent,
    Circuit,
    ComponentDefinition,
    Courtyard,
    Net,
    Placement,
    Product,
)
from pcb.harness.base.pcbnew.land_pattern import LandPattern
from pcb.harness.base.pcbnew.outline import BoardOutline
from pcb.harness.base.pcbnew.pad import Pad
from pcb.harness.base.pcbnew.point import Point
from pcb.harness.base.pcbnew.route import CopperLayer, Trace, Via


class Pin(StrEnum):
    """Logical contacts for a simple two-pad test component."""

    A = "1"
    B = "2"


class Nets(Net):
    """The design nets assigned to the two test pins."""

    POWER = "+3V3"
    GROUND = "GND"


def sample_board(*, pattern: bool = True, outline: bool = True) -> Circuit[Nets]:
    """Declare a two-contact board whose output is easy to inspect natively."""
    board = Circuit(Nets, outline=BoardOutline(20, 10) if outline else None)
    land = (
        LandPattern(
            Pin, (Pad(Pin.A, Point(-1, 0), 1, 1), Pad(Pin.B, Point(1, 0), 1, 1))
        )
        if pattern
        else None
    )
    definition = ComponentDefinition(
        Product("TEST", "Maker", "Part", "Pkg", (1, 1, 1), "drawing"),
        Pin,
        Courtyard(4, 3),
        land_pattern=land,
    )
    board.place(
        BoardComponent,
        reference="U1",
        definition=definition,
        placement=Placement(0, 0),
        purpose="fixture",
        pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
    )
    return board


@unittest.skipUnless(importlib.util.find_spec("pcbnew"), "KiCad Python module required")
class RenderBoardTest(unittest.TestCase):
    """Inspect native KiCad objects without running the DRC checker."""

    def test_board_has_outline_footprint_and_typed_nets(self) -> None:
        """The board includes edge graphics, a footprint, and declared pad nets."""
        from pcb.harness.base.pcbnew.render.board import render_board

        native = render_board(sample_board())
        # Four drawings represent the rectangle's four Edge.Cuts sides.
        self.assertEqual(len(list(native.GetDrawings())), 4)
        footprint = native.FindFootprintByReference("U1")
        self.assertIsNotNone(footprint)
        assert footprint is not None
        pads = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
        # Each native pad number must point to the net assigned to that logical pin.
        self.assertEqual(pads, {"1": "+3V3", "2": "GND"})

    def test_duplicate_physical_pads_share_their_logical_pin_net(self) -> None:
        """A four-leg style package keeps both lands of one contact on one net."""
        from pcb.harness.base.pcbnew.render.board import render_board

        board = Circuit(Nets, outline=BoardOutline(20, 10))
        pattern = LandPattern(
            Pin,
            (
                Pad(Pin.A, Point(-1, 0.5), 0.5, 0.5),
                Pad(Pin.A, Point(-1, -0.5), 0.5, 0.5, number="1b"),
                Pad(Pin.B, Point(1, 0), 0.5, 0.5),
            ),
        )
        definition = ComponentDefinition(
            Product("SW", "Maker", "Demo", "switch", (2, 1, 1), "drawing"),
            Pin,
            Courtyard(3, 2),
            land_pattern=pattern,
        )
        board.place(
            BoardComponent,
            reference="SW1",
            definition=definition,
            placement=Placement(0, 0),
            purpose="duplicate contact fixture",
            pins={Pin.A: Nets.POWER, Pin.B: Nets.GROUND},
        )
        footprint = render_board(board).FindFootprintByReference("SW1")
        assert footprint is not None
        nets = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
        self.assertEqual(nets, {"1": "+3V3", "1b": "+3V3", "2": "GND"})

    def test_missing_outline_or_land_pattern_is_rejected(self) -> None:
        """PCB conversion requires an outline and package pad geometry."""
        from pcb.harness.base.pcbnew.render.board import render_board

        with self.assertRaisesRegex(ValueError, "outline"):
            render_board(sample_board(outline=False))
        with self.assertRaisesRegex(ValueError, "land pattern"):
            render_board(sample_board(pattern=False))

    def test_undeclared_route_net_is_rejected(self) -> None:
        """Routes cannot name a net absent from this circuit's typed enum."""
        from pcb.harness.base.pcbnew.render.board import render_board

        board = sample_board()

        class Other(Net):
            SIGNAL = "SIGNAL"

        # Runtime validation also protects callers that bypass static typing.
        with self.assertRaisesRegex(ValueError, "board Net enum"):
            board.trace(
                cast(
                    Trace[Nets],
                    Trace(Other.SIGNAL, Point(0, 0), Point(1, 0), CopperLayer.TOP, 0.2),
                )
            )
        board.trace(Trace(Nets.POWER, Point(0, 0), Point(1, 0), CopperLayer.TOP, 0.2))
        board.via(Via(Nets.POWER, Point(0, 0), 0.7, 0.3))
        # One declared trace and one via become two native track-like objects.
        self.assertEqual(len(list(render_board(board).GetTracks())), 2)

    def test_copper_centerline_and_width_must_fit_board(self) -> None:
        """A trace whose half-width crosses the edge is rejected."""
        from pcb.harness.base.pcbnew.render.board import render_board

        board = sample_board()
        board.trace(
            Trace(Nets.POWER, Point(9.8, 0), Point(9.9, 0), CopperLayer.TOP, 0.4)
        )
        with self.assertRaisesRegex(ValueError, "edge"):
            render_board(board)

    def test_via_diameter_must_fit_board(self) -> None:
        """A via whose radius crosses the edge is rejected."""
        from pcb.harness.base.pcbnew.render.board import render_board

        board = sample_board()
        board.via(Via(Nets.POWER, Point(9.8, 0), 0.7, 0.3))
        with self.assertRaisesRegex(ValueError, "edge"):
            render_board(board)

    def test_saved_board_can_be_opened_by_kicad(self) -> None:
        """KiCad can reload the saved file and recover its component reference."""
        import pcbnew

        with tempfile.TemporaryDirectory() as directory:
            path = sample_board().write_board(Path(directory) / "sample.kicad_pcb")
            self.assertTrue(path.exists())
            loaded = pcbnew.LoadBoard(str(path))
            # Reopening proves basic file serialization, not electrical DRC or safety.
            self.assertIsNotNone(loaded.FindFootprintByReference("U1"))
