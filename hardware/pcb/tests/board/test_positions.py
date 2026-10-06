"""The pick-and-place file names every part's package (manufacturing review, S4c).

Why: an assembly house needs the package per row of `positions.csv`; a missing value is
easy to overlook, so every placed row must match the footprint's package field.
"""

import csv
import os
import unittest
from pathlib import Path

import pcbnew

PCB_ROOT = Path(__file__).resolve().parents[2]


class PositionsTest(unittest.TestCase):
    """The position file and the board agree on every placed part's package."""

    def test_every_placement_row_carries_the_approved_package(self) -> None:
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        rows = list(csv.DictReader((output / "positions.csv").read_text().splitlines()))
        board = pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))
        packages = {
            f.GetReference(): f.GetFieldText("Package")
            for f in board.GetFootprints()
            if f.HasFieldByName("Package")
        }
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(reference=row["Ref"]):
                self.assertTrue(row["Package"])
                self.assertEqual(row["Package"], packages[row["Ref"]])
