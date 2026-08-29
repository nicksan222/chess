"""Reusable cells, parts, and net names."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ELECTRONICS = Path(__file__).resolve().parents[1]
if str(ELECTRONICS) not in sys.path:
    sys.path.insert(0, str(ELECTRONICS))

from blocks.square import add_column_pullup, add_led_cell, add_reed_cell
from core.canvas import SheetInfo, load_schematic
from components import DIODE, REED, WS2812B
from core.names import led_chain_order, parse_square, square


class NamesTest(unittest.TestCase):
    def test_square_round_trip(self) -> None:
        self.assertEqual(square(0, 0), "A1")
        self.assertEqual(square(7, 7), "H8")
        self.assertEqual(parse_square("e4"), (4, 3))
        self.assertEqual(len(led_chain_order()), 64)
        self.assertEqual(led_chain_order()[0][0], "A1")
        self.assertEqual(led_chain_order()[7][0], "H1")
        self.assertEqual(led_chain_order()[8][0], "H2")


class PartsAndCellsTest(unittest.TestCase):
    def test_catalog_covers_square_parts(self) -> None:
        self.assertEqual(REED.lib, "REED")
        self.assertEqual(DIODE.lib, "DIODE")
        self.assertEqual(WS2812B.lib, "WS2812B")

    def test_one_square_cell_is_reusable(self) -> None:
        sch = load_schematic(SheetInfo(title="cell", project="cell"))
        add_column_pullup(sch, ref="R1", col_x=12.0, y=0.0, col_net="COL_0")
        add_reed_cell(
            sch,
            square_name="A1",
            reed_ref="SW1",
            diode_ref="D1",
            col_x=12.0,
            y=4.0,
            row_net="ROW_0",
        )
        add_led_cell(
            sch,
            square_name="A1",
            chain_index=1,
            led_ref="U1",
            cap_ref="C1",
            x=14.0,
            y=14.0,
        )
        libs = [spec.lib for spec in sch.symbols]
        self.assertEqual(libs.count("REED"), 1)
        self.assertEqual(libs.count("DIODE"), 1)
        self.assertEqual(libs.count("WS2812B"), 1)
        self.assertEqual(libs.count("R"), 1)
        self.assertEqual(libs.count("C"), 1)


if __name__ == "__main__":
    unittest.main()
