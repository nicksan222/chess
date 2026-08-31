"""What gets written, and the gate that decides whether it may be shipped.

The most important test here is the last one: the manufacturing package must not
exist while any connection is unrouted. A fab cannot tell an unrouted board from
a finished one, so that gate is the only thing standing between a valid file and
a useless order.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from gerbonara import LayerStack  # noqa: E402
from gerbonara.graphic_objects import Flash, Line, Region  # noqa: E402

from core import connectivity, layers, nets, placement, routing, rules  # noqa: E402

GENERATED = PCB_ROOT / "generated"
STACK_DIRECTORY = GENERATED / "gerber"


def load_generator():
    path = PCB_ROOT / "projects" / "board" / "generate.py"
    spec = importlib.util.spec_from_file_location("pcb_board_generate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArtworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.placements = placement.build()
        cls.artwork, cls.counts = routing.build_artwork(cls.placements)
        cls.pad_net = nets.pad_nets()
        cls.stack = layers.build_stack(cls.placements, cls.artwork, cls.pad_net)

    def test_the_stack_has_every_layer_a_fab_expects(self) -> None:
        self.assertEqual(
            {f"{side} {use}" for side, use in self.stack.graphic_layers},
            {
                "mechanical outline",
                "top copper",
                "top mask",
                "top silk",
                "top paste",
                "bottom copper",
                "bottom mask",
                "bottom silk",
                "bottom paste",
            },
        )
        self.assertIsNotNone(self.stack.drill_pth)

    def test_the_outline_is_the_board_size(self) -> None:
        board = layers.Board()
        width, height = self.stack.outline.size("mm")
        self.assertAlmostEqual(float(width), board.width, delta=0.3)
        self.assertAlmostEqual(float(height), board.height, delta=0.3)

    def test_every_through_hole_pad_gets_a_drill(self) -> None:
        expected = sum(
            1
            for item in self.placements
            for _net, _number, _position, pad in item.pads()
            if pad.plated_through
        )
        drills = len(self.stack.drill_pth.objects)
        self.assertEqual(drills, expected + len(self.artwork.vias))

    def test_only_surface_mount_pads_get_paste(self) -> None:
        paste = self.stack.graphic_layers[("top", "paste")]
        expected = sum(
            1
            for item in self.placements
            for _net, _number, _position, pad in item.pads()
            if not pad.plated_through
        )
        self.assertEqual(len(paste.objects), expected)
        # 64 LEDs with six pads each, and nothing else is surface-mount.
        self.assertEqual(expected, 64 * 6)

    def test_nothing_is_drawn_outside_the_board(self) -> None:
        """A fab trims anything past the outline, silkscreen included."""
        board = layers.Board()
        outside = [
            (start, end)
            for start, end in self.artwork.silk_lines
            if not board.contains(*start) or not board.contains(*end)
        ]
        self.assertEqual(outside[:4], [], f"{len(outside)} silk segments off-board")
        for trace in self.artwork.traces:
            self.assertTrue(board.contains(*trace.start), trace.net)
            self.assertTrue(board.contains(*trace.end), trace.net)
        for via in self.artwork.vias:
            self.assertTrue(board.contains(*via.at), via.net)

    def test_the_written_layers_fit_inside_the_outline(self) -> None:
        board = layers.Board()
        for (side, use), layer in self.stack.graphic_layers.items():
            if not layer.objects or use == "outline":
                continue
            width, height = (float(value) for value in layer.size("mm"))
            with self.subTest(layer=f"{side} {use}"):
                self.assertLessEqual(width, board.width + 0.5)
                self.assertLessEqual(height, board.height + 0.5)

    def test_the_led_chain_is_fully_routed(self) -> None:
        """63 links, clock and data, is the whole chain."""
        self.assertEqual(self.counts["led_chain_links"], 2 * 63)

    def test_every_surface_mount_ground_pad_reaches_the_pour(self) -> None:
        self.assertEqual(self.counts["ground_stitches"], 64)
        self.assertEqual(
            len([via for via in self.artwork.vias if via.net == "GND"]), 64
        )


class GroundPourTest(unittest.TestCase):
    """A pour without clearances shorts the board; this is that check."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.placements = placement.build()
        cls.artwork, _counts = routing.build_artwork(cls.placements)
        cls.pad_net = nets.pad_nets()
        cls.stack = layers.build_stack(cls.placements, cls.artwork, cls.pad_net)
        cls.bottom = cls.stack.graphic_layers[("bottom", "copper")]

    def test_the_pour_is_one_region(self) -> None:
        regions = [o for o in self.bottom.objects if isinstance(o, Region)]
        self.assertEqual(len(regions), 1)
        self.assertTrue(regions[0].polarity_dark)

    def test_every_pad_not_on_ground_is_cleared_out_of_the_pour(self) -> None:
        cleared = {
            (round(o.x, 3), round(o.y, 3))
            for o in self.bottom.objects
            if isinstance(o, Flash) and not o.polarity_dark
        }
        board = layers.Board()
        missing = []
        for item in self.placements:
            for net_number, number, (x, y), pad in item.pads():
                if not pad.plated_through:
                    continue
                if self.pad_net.get((item.reference, net_number)) == "GND":
                    continue
                at = board.to_gerber(x, y)
                if (round(at[0], 3), round(at[1], 3)) not in cleared:
                    missing.append(f"{item.reference}.{number}")
        self.assertEqual(missing[:8], [], f"{len(missing)} pads would short to ground")

    def test_ground_pads_are_repainted_so_they_stay_attached(self) -> None:
        """A clearance would otherwise isolate the very pads that need the pour."""
        objects = self.bottom.objects
        dark_flashes = [
            index
            for index, o in enumerate(objects)
            if isinstance(o, Flash) and o.polarity_dark
        ]
        clear_flashes = [
            index
            for index, o in enumerate(objects)
            if isinstance(o, Flash) and not o.polarity_dark
        ]
        self.assertTrue(dark_flashes)
        self.assertTrue(clear_flashes)
        # Painting order matters: the reattached pads must come last.
        self.assertGreater(min(dark_flashes), max(clear_flashes))


class RoundTripTest(unittest.TestCase):
    """What was written must read back as what was meant."""

    @classmethod
    def setUpClass(cls) -> None:
        if not (STACK_DIRECTORY / "chess-board-F_Cu.gbr").is_file():
            raise unittest.SkipTest("run ./tools/pcb to generate the stack first")
        cls.stack = LayerStack.open(STACK_DIRECTORY)
        cls.placements = placement.build()
        cls.artwork, _counts = routing.build_artwork(cls.placements)

    def test_traces_survive_being_written_and_read(self) -> None:
        top = self.stack.graphic_layers[("top", "copper")]
        lines = [o for o in top.objects if isinstance(o, Line)]
        self.assertEqual(len(lines), len(self.artwork.traces))

    def test_a_known_chain_link_is_present_at_the_right_place(self) -> None:
        board = layers.Board()
        positions = routing.pad_positions(self.placements)
        start = board.to_gerber(*positions[("U6", "5")])
        end = board.to_gerber(*positions[("U7", "3")])
        top = self.stack.graphic_layers[("top", "copper")]
        found = [
            o
            for o in top.objects
            if isinstance(o, Line)
            and {(round(o.x1, 2), round(o.y1, 2)), (round(o.x2, 2), round(o.y2, 2))}
            == {(round(start[0], 2), round(start[1], 2)),
                (round(end[0], 2), round(end[1], 2))}
        ]
        self.assertEqual(len(found), 1, "the A1 to B1 data link is missing")

    def test_traces_are_the_width_the_rules_chose(self) -> None:
        top = self.stack.graphic_layers[("top", "copper")]
        widths = {
            round(float(o.aperture.diameter), 3)
            for o in top.objects
            if isinstance(o, Line)
        }
        self.assertEqual(widths, {rules.TRACE_WIDTH_MM})


class GateTest(unittest.TestCase):
    """The package must not exist while the board would not work."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_generator()
        _placements, _artwork, _stack, cls.statuses, _counts = cls.module.assemble()
        cls.summary = connectivity.summary(cls.statuses)

    def test_the_report_accounts_for_every_multi_pad_connection(self) -> None:
        netlist = __import__("core.sources", fromlist=["sources"]).netlist()
        expected = sum(
            1 for entry in netlist["connections"] if len(entry["pads"]) >= 2
        )
        self.assertEqual(self.summary["connections"], expected)

    def test_single_pad_connections_are_not_counted_as_work(self) -> None:
        """They are deliberate no-connects, not unrouted nets."""
        names = {status.name for status in self.statuses}
        for deliberate in ("LED_DATA_LAST", "LED_CLK_LAST"):
            self.assertNotIn(deliberate, names)

    def test_the_led_chain_reports_as_routed(self) -> None:
        """Only the links between LEDs; the buffer feeding the chain is not one."""
        chain = re.compile(r"^(LED_[DC]\d+|unnamed:U\d+\.[3-6])$")
        unrouted = sorted(
            status.name
            for status in self.statuses
            if not status.routed and chain.match(status.name)
        )
        self.assertEqual(unrouted, [], f"chain links unrouted: {unrouted[:5]}")

    def test_the_buffered_led_signals_are_still_outstanding(self) -> None:
        """Stated so the gate cannot pass while the chain has no source."""
        unrouted = {status.name for status in self.statuses if not status.routed}
        if not self.summary["complete"]:
            self.assertIn("LED_DATA_5V", unrouted)

    def test_ground_reports_as_routed(self) -> None:
        ground = next(s for s in self.statuses if s.name == "GND")
        self.assertTrue(ground.routed, f"ground is in {ground.islands} islands")

    def test_the_outstanding_work_is_named_honestly(self) -> None:
        report = connectivity.report(self.statuses)
        if self.summary["complete"]:
            self.assertIn("Every design contract connection", report)
        else:
            self.assertIn("SQ_* reed sense lines", report)
            self.assertIn("links missing", report)

    def test_the_package_exists_only_when_everything_is_routed(self) -> None:
        package = self.module.PACKAGE_PATH
        if self.summary["complete"]:
            self.assertTrue(package.is_file(), "a finished board should be packaged")
        else:
            self.assertFalse(
                package.is_file(),
                "an unrouted board must not be shipped as a fabrication package",
            )

    def test_the_report_is_published(self) -> None:
        self.assertTrue(self.module.REPORT_PATH.is_file())
        text = self.module.REPORT_PATH.read_text()
        self.assertIn("do not edit by", text)
        self.assertIn("connections routed", text)


if __name__ == "__main__":
    unittest.main()
