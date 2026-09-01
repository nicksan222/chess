"""Where the parts sit, checked against the board and against each other.

Placement is the half of layout this domain does fully, so it is the half worth
testing hard. Two parts on top of each other, or a pad off the edge of the board,
are both mistakes a fab will happily manufacture.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from core import placement, sources  # noqa: E402
from core.board import Board  # noqa: E402


class PlacementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shared = sources.dimensions()
        cls.netlist = sources.netlist()
        cls.placements = placement.build()
        cls.board = Board()
        cls.by_reference = {p.reference: p for p in cls.placements}

    def test_every_board_part_is_placed(self) -> None:
        expected = set(self.netlist["components"])
        self.assertEqual(set(self.by_reference), expected)
        self.assertEqual(len(self.placements), len(expected))
        self.assertFalse(
            any(
                entry["lib"] == "DIP_SOCKET"
                for entry in self.netlist["components"].values()
            )
        )

    def test_no_two_parts_overlap(self) -> None:
        collisions = []
        for first in range(len(self.placements)):
            for second in range(first + 1, len(self.placements)):
                a = self.placements[first].courtyard()
                b = self.placements[second].courtyard()
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    collisions.append(
                        (
                            self.placements[first].reference,
                            self.placements[second].reference,
                        )
                    )
        self.assertEqual(collisions, [], f"overlapping parts: {collisions[:8]}")

    def test_every_part_is_inside_the_board(self) -> None:
        for item in self.placements:
            x0, y0, x1, y1 = item.courtyard()
            with self.subTest(reference=item.reference):
                self.assertGreaterEqual(x0, self.board.x_min)
                self.assertLessEqual(x1, self.board.x_max)
                self.assertGreaterEqual(y0, self.board.y_min)
                self.assertLessEqual(y1, self.board.y_max)

    def test_every_pad_is_inside_the_board(self) -> None:
        for item in self.placements:
            for _net_number, number, (x, y), _pad in item.pads():
                with self.subTest(reference=item.reference, pad=number):
                    self.assertTrue(self.board.contains(x, y))


class GridAlignmentTest(unittest.TestCase):
    """The copper has to agree with the plastic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.shared = sources.dimensions()
        cls.netlist = sources.netlist()
        cls.by_reference = {p.reference: p for p in placement.build()}

    def test_every_led_sits_where_the_plate_has_a_diffuser_pocket(self) -> None:
        expected = {
            (x, y) for _row, _column, x, y in self.shared.BOARD_LED_POSITIONS_MM
        }
        placed = {
            (item.x, item.y)
            for reference, item in self.by_reference.items()
            if self.netlist["components"][reference]["lib"] == "SK9822"
        }
        self.assertEqual(placed, expected)

    def test_every_hall_sensor_sits_at_a_square_centre(self) -> None:
        expected = {
            (x, y) for _row, _column, x, y in self.shared.BOARD_HALL_POSITIONS_MM
        }
        placed = {
            (item.x, item.y)
            for reference, item in self.by_reference.items()
            if self.netlist["components"][reference]["lib"] == "HALL"
        }
        self.assertEqual(placed, expected)

    def test_every_button_sits_under_a_bezel_hole(self) -> None:
        expected = set(self.shared.PANEL_BUTTON_POSITIONS_MM)
        placed = {
            (item.x, item.y)
            for reference, item in self.by_reference.items()
            if self.netlist["components"][reference]["lib"] == "BUTTON"
        }
        self.assertEqual(placed, expected)

    def test_the_pi_header_sits_in_the_bay_the_case_provides(self) -> None:
        header = self.by_reference["J1"]
        self.assertEqual((header.x, header.y), tuple(self.shared.PI_BAY_CENTER_MM))

    def test_square_names_reconcile_the_two_row_conventions(self) -> None:
        """CAD counts rows from the far side; the design contract names ranks near-first."""
        centres = placement.square_centres(self.shared)
        self.assertEqual(len(centres), 64)
        half = self.shared.PLAYING_SPAN_MM / 2.0
        offset = self.shared.SQUARE_SIZE_MM / 2.0
        self.assertEqual(centres["A1"], (-half + offset, -half + offset))
        self.assertEqual(centres["H8"], (half - offset, half - offset))
        self.assertEqual(centres["A8"], (-half + offset, half - offset))

    def test_expanders_sit_beside_the_quadrant_they_serve(self) -> None:
        square_centres = placement.square_centres(self.shared)
        for reference, entry in self.netlist["components"].items():
            if entry["lib"] != "MCP23017":
                continue
            item = self.by_reference[reference]
            quadrant = entry["extras"]["Quadrant"]
            first, last = quadrant.split("-")
            centre = tuple(
                (left + right) / 2.0
                for left, right in zip(
                    square_centres[first], square_centres[last], strict=True
                )
            )
            with self.subTest(expander=reference):
                self.assertEqual(
                    (item.x, item.y),
                    self.shared.EXPANDER_POSITIONS_BY_QUADRANT_MM[quadrant],
                )
                # Preserve the short quadrant fanout and avoid the centre LED.
                self.assertAlmostEqual(item.x - centre[0], 14.0, places=6)
                self.assertAlmostEqual(item.y - centre[1], 0.0, places=6)

    def test_hall_output_traces_stay_short(self) -> None:
        """The whole reason for four expanders instead of one."""
        expanders = {
            reference: self.by_reference[reference]
            for reference, entry in self.netlist["components"].items()
            if entry["lib"] == "MCP23017"
        }
        sensors = {
            reference: self.by_reference[reference]
            for reference, entry in self.netlist["components"].items()
            if entry["lib"] == "HALL"
        }
        worst = 0.0
        for connection in self.netlist["connections"]:
            pads = [tuple(pad) for pad in connection["pads"]]
            sensor = next((r for r, _p in pads if r in sensors), None)
            expander = next((r for r, _p in pads if r in expanders), None)
            if sensor is None or expander is None:
                continue
            distance = (
                (sensors[sensor].x - expanders[expander].x) ** 2
                + (sensors[sensor].y - expanders[expander].y) ** 2
            ) ** 0.5
            worst = max(worst, distance)
        self.assertGreater(worst, 0.0, "no Hall-to-expander pairs found")
        self.assertLess(worst, 110.0, f"longest Hall run is {worst:.1f} mm")


if __name__ == "__main__":
    unittest.main()
