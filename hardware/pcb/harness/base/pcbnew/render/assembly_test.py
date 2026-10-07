"""Assembly outputs must cover every real part with native XY/rotation intact."""

import csv
import tempfile
import unittest
from pathlib import Path

from pcb.board.board import Board

from .assembly import write_assembly


class AssemblyTest(unittest.TestCase):
    def test_smd_and_manual_lists_partition_the_board_and_bom_totals_match(
        self,
    ) -> None:
        board = Board()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            positions = root / "positions.csv"
            with positions.open("w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
                )
                for i, part in enumerate(board.components()):
                    writer.writerow(
                        (part.reference, "native", "", i + 0.125, -i, 90, "top")
                    )
            write_assembly(board, root)

            def rows(name: str) -> list[dict[str, str]]:
                with (root / name).open() as file:
                    return list(csv.DictReader(file))

            enriched = rows("positions.csv")
            self.assertTrue(all(row["Package"] and row["Val"] for row in enriched))
            smd, manual = rows("assembly-smd.csv"), rows("assembly-through-hole.csv")
            references = {part.reference for part in board.components()}
            self.assertEqual(
                {row["Designator"] for row in smd}
                | {row["Designator"] for row in manual},
                references,
            )
            self.assertFalse(
                {row["Designator"] for row in smd}
                & {row["Designator"] for row in manual}
            )
            self.assertEqual(
                sum(int(row["Quantity"]) for row in rows("assembly-bom.csv")),
                len(references),
            )
            self.assertIn("SW1", {row["Designator"] for row in manual})
            self.assertIn("HS1", {row["Designator"] for row in smd})
            self.assertEqual(enriched[0]["PosX"], "0.125")
            self.assertEqual(enriched[0]["Rot"], "90")
            self.assertIn("200 mm", (root / "harness.md").read_text())
            self.assertIn("180 mm", (root / "harness.md").read_text())
            self.assertIn(
                "POWER_HARNESS_HOUSING",
                {row["Product"] for row in rows("harness-bom.csv")},
            )
            harness = {
                row["Product"]: int(row["Quantity"]) for row in rows("harness-bom.csv")
            }
            for product in ("BARREL_JACK", "POWER_SWITCH", "OLED_MODULE"):
                self.assertEqual(harness[product], 1)
            positions.write_text("Ref,Val,Package,PosX,PosY,Rot,Side\n")
            with self.assertRaisesRegex(ValueError, "coverage"):
                write_assembly(board, root)
