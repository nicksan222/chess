"""Semantic PR-report comparisons."""

import unittest

from pcb.pr_report import (
    BoardSnapshot,
    _component_changes,
    _copper_changes,
    _net_changes,
    _placement_changes,
    _rule_changes,
)


class PullRequestReportTest(unittest.TestCase):
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
