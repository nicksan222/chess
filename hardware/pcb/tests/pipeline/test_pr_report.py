"""Semantic PR-report comparisons.

Role: tests for `pr_report.py` using small hand-written netlist/layout/copper data,
so no KiCad, Git or generated files are needed. They check that real design changes
are described in reviewer terms, and that an unchanged design is flagged so CI can
suppress the comment.
"""

import json
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

from pcb.pr_report import (
    BoardSnapshot,
    CopperBounds,
    CopperPoint,
    CopperTrack,
    CopperVia,
    CopperZone,
    _component_changes,
    _copper_changes,
    _net_changes,
    _placement_changes,
    _rule_changes,
    build_report,
)


class PullRequestReportTest(unittest.TestCase):
    def test_orders_copper_points_by_x_then_y(self):
        # `CopperPoint` ordering is used to give track endpoints a canonical order
        # (so a segment compares equal in either direction); dataclass order is
        # x first, then y, and equal points tie.
        points = [
            CopperPoint(2.0, 0.0),
            CopperPoint(1.0, 3.0),
            CopperPoint(1.0, 2.0),
        ]

        self.assertEqual(
            sorted(points),
            [CopperPoint(1.0, 2.0), CopperPoint(1.0, 3.0), CopperPoint(2.0, 0.0)],
        )

    def _report(self, components: Mapping[str, object]) -> str:
        """Run `build_report` end to end with the given current components.

        The base side is an empty design and every other input is "no change".
        Git lookups and KiCad board loading are patched out; the rest (reading the
        current files from a temp directory, rendering Markdown) is real.
        """
        document: dict[str, object] = {
            "projects": {
                "board": {
                    "revision": "test board",
                    "components": dict(components),
                    "nets": {},
                }
            }
        }
        base_document: dict[str, object] = {
            "projects": {
                "board": {
                    "revision": "test board",
                    "components": {},
                    "nets": {},
                }
            }
        }
        layout: dict[str, object] = {"placements": {}, "rules": {}}
        board = BoardSnapshot(
            tracks=frozenset(),
            vias=frozenset(),
            zones=frozenset(),
            board_sha256="same",
        )

        # Stand-in for reading the base ref's committed files with `git show`.
        def base_json(_ref: str, name: str) -> dict[str, object]:
            return base_document if name == "netlist.json" else layout

        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory)
            (current / "netlist.json").write_text(json.dumps(document))
            (current / "layout.json").write_text(json.dumps(layout))
            (current / "manifest.json").write_text(json.dumps({"checks": ["DRC"]}))
            (current / "erc.json").write_text(json.dumps({"sheets": []}))
            (current / "drc.json").write_text(
                json.dumps(
                    {
                        "violations": [],
                        "unconnected_items": [],
                        "schematic_parity": [],
                    }
                )
            )
            with (
                patch("pcb.pr_report._base_json", side_effect=base_json),
                patch("pcb.pr_report.board_snapshot", return_value=board),
                patch("pcb.pr_report._base_board", return_value=board),
            ):
                return build_report(
                    base_ref="main",
                    head_ref="head",
                    current=current,
                    repository=None,
                    run_url=None,
                )

    def test_marks_unchanged_board_for_comment_suppression(self):
        # Base and current both empty: the hidden marker must say "false".
        report = self._report({})

        self.assertIn("<!-- pcb-design-changed: false -->", report)
        self.assertNotIn("Changed files", report)

    def test_marks_semantic_board_change_for_comment_publication(self):
        # A new component is a semantic change: marker "true" and an "Added" line.
        report = self._report(
            {"TP1": {"description": "test point", "value": "", "package": "SMD"}}
        )

        self.assertIn("<!-- pcb-design-changed: true -->", report)
        self.assertIn("Added `TP1`", report)

    def test_reports_component_and_wiring_changes(self):
        # R1's value changes (modified), TP1 is new (added), and net SDA loses U1.2
        # and gains U1.3 and TP1.1 (rewired); check counts and detail text.
        before = {
            "components": {
                "R1": {"description": "pull-up", "value": "10k", "package": "0603"}
            },
            "nets": {"SDA": [["R1", "1"], ["U1", "2"]]},
        }
        after = {
            "components": {
                "R1": {"description": "pull-up", "value": "4.7k", "package": "0603"},
                "TP1": {"description": "test point", "value": "", "package": "SMD"},
            },
            "nets": {"SDA": [["R1", "1"], ["U1", "3"], ["TP1", "1"]]},
        }

        component_summary, components = _component_changes(before, after)
        net_summary, nets = _net_changes(before, after)

        self.assertIn("+1 added", component_summary)
        self.assertIn("1 modified", component_summary)
        self.assertTrue(any("Added `TP1`" in line for line in components))
        self.assertTrue(any("Changed `R1`: value" in line for line in components))
        self.assertIn("1 rewired", net_summary)
        self.assertEqual(nets, ["Rewired `SDA`: +TP1.1, +U1.3, −U1.2"])

    def test_reports_placement_and_nested_rule_changes(self):
        # A moved footprint ([x, y, rotation]) and a design rule nested two levels
        # deep must both be reported, the latter under its dotted key.
        before = {
            "placements": {"U1": [1.0, 2.0, 0.0]},
            "rules": {"defaults": {"clearance": 0.2}},
        }
        after = {
            "placements": {"U1": [2.0, 3.0, 90.0]},
            "rules": {"defaults": {"clearance": 0.3}},
        }

        placement_summary, placements = _placement_changes(before, after)
        rule_summary, rules = _rule_changes(before, after)

        self.assertEqual(placement_summary, "1 footprints (1 changed)")
        self.assertEqual(placements, ["Moved `U1`: [1.0, 2.0, 0.0] → [2.0, 3.0, 90.0]"])
        self.assertEqual(rule_summary, "1 settings changed")
        self.assertEqual(rules, ["`defaults.clearance`: `0.2` → `0.3`"])

    def test_groups_added_and_removed_copper_by_net_and_layer(self):
        # Old board: one GND track. New board: one +5V track, a via and a GND zone.
        # Expect per-net/layer grouping, a net-zero segment count (1 removed, 1
        # added) and four geometry changes in total.
        old_track = CopperTrack(
            "GND", "B.Cu", CopperPoint(0.0, 0.0), CopperPoint(1.0, 0.0), 0.2
        )
        new_track = CopperTrack(
            "+5V", "F.Cu", CopperPoint(0.0, 0.0), CopperPoint(2.0, 0.0), 0.3
        )
        old = BoardSnapshot(
            tracks=frozenset({old_track}),
            vias=frozenset(),
            zones=frozenset(),
            board_sha256="old",
        )
        new = BoardSnapshot(
            tracks=frozenset({new_track}),
            vias=frozenset(
                {
                    CopperVia(
                        "+5V",
                        CopperPoint(2.0, 0.0),
                        0.8,
                        0.4,
                        ("F.Cu", "B.Cu"),
                    )
                }
            ),
            zones=frozenset(
                {
                    CopperZone(
                        "GND",
                        ("B.Cu",),
                        CopperBounds(0.0, 0.0, 10.0, 10.0),
                    )
                }
            ),
            board_sha256="new",
        )

        summary, details = _copper_changes(old, new)

        self.assertIn("1 segments (0)", summary)
        self.assertIn("1 vias (+1)", summary)
        self.assertIn("4 geometry changes", summary)
        self.assertIn("`+5V` on F.Cu: +1 / −0 track segments", details)
        self.assertIn("`GND` on B.Cu: +0 / −1 track segments", details)
        self.assertIn("`+5V`: +1 / −0 vias", details)
        self.assertIn("Added `GND` copper zone on B.Cu", details)


if __name__ == "__main__":
    unittest.main()
