"""Semantic PR-report comparisons."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pcb.pr_report import (
    BoardSnapshot,
    _component_changes,
    _copper_changes,
    _net_changes,
    _placement_changes,
    _rule_changes,
    build_report,
)


class PullRequestReportTest(unittest.TestCase):
    def _report(self, components):
        document = {
            "projects": {
                "board": {
                    "revision": "test board",
                    "components": components,
                    "nets": {},
                }
            }
        }
        base_document = {
            "projects": {
                "board": {
                    "revision": "test board",
                    "components": {},
                    "nets": {},
                }
            }
        }
        layout = {"placements": {}, "rules": {}}
        board = BoardSnapshot(
            tracks=frozenset(),
            vias=frozenset(),
            zones=frozenset(),
            board_sha256="same",
        )
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
                patch(
                    "pcb.pr_report._base_json",
                    side_effect=lambda _ref, name: (
                        base_document if name == "netlist.json" else layout
                    ),
                ),
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
        report = self._report({})

        self.assertIn("<!-- pcb-design-changed: false -->", report)
        self.assertNotIn("Changed files", report)

    def test_marks_semantic_board_change_for_comment_publication(self):
        report = self._report(
            {"TP1": {"description": "test point", "value": "", "package": "SMD"}}
        )

        self.assertIn("<!-- pcb-design-changed: true -->", report)
        self.assertIn("Added `TP1`", report)

    def test_reports_component_and_wiring_changes(self):
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
        old_track = ("GND", "B.Cu", (0.0, 0.0), (1.0, 0.0), 0.2)
        new_track = ("+5V", "F.Cu", (0.0, 0.0), (2.0, 0.0), 0.3)
        old = BoardSnapshot(
            tracks=frozenset({old_track}),
            vias=frozenset(),
            zones=frozenset(),
            board_sha256="old",
        )
        new = BoardSnapshot(
            tracks=frozenset({new_track}),
            vias=frozenset({("+5V", (2.0, 0.0), 0.8, 0.4, ("F.Cu", "B.Cu"))}),
            zones=frozenset({("GND", ("B.Cu",), (0.0, 0.0, 10.0, 10.0))}),
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
