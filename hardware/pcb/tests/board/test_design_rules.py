"""The U74 fine-pitch exception stays scoped to U74 (lead-approved, S4b).

`output/exports.render_design_rules()` writes the KiCad custom rules beside the
board: board-wide 0.30 mm clearance and 0.31 mm tracks, then 0.15 / 0.20 mm only for
U74's pads and copper crossing its courtyard. These tests check the rule text names
U74 alone (a mutation naming another part fails), and that the routed board needs
the exception nowhere else: KiCad's DRC without the U74 rules may only flag items at
U74.
"""

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict, cast

import pcbnew

from pcb.definition import rules
from pcb.definition.output import exports

PCB_ROOT = Path(__file__).resolve().parents[2]


class NetClass(TypedDict):
    """One KiCad netclass entry (clearance and track width) as read from the project JSON."""

    clearance: float
    track_width: float


class NetClasses(TypedDict):
    """The `classes` list inside the project's net settings."""

    classes: list[NetClass]


class NetSettings(TypedDict):
    """The `net_settings` section of the project file."""

    net_settings: NetClasses


class Position(TypedDict):
    """An (x, y) position in a DRC report."""

    x: float
    y: float


class DrcItem(TypedDict):
    """One item (description, position, id) a DRC violation refers to."""

    description: str
    pos: Position
    uuid: str


class Violation(TypedDict):
    """One DRC violation: type, description and the items involved."""

    type: str
    description: str
    items: list[DrcItem]


class DrcReport(TypedDict):
    """The part of a KiCad DRC JSON report the tests read."""

    violations: list[Violation]


def exception_scopes(text: str) -> set[str]:
    """Footprints named by the rules that loosen clearance or track width."""
    scopes: set[str] = set()
    found: list[str] = re.findall(
        r'\(rule "[^"]*"(.*?)\)\)\s*(?=\(rule|\Z)', text, re.DOTALL
    )
    for rule in found:
        loosened = re.search(r"\(min ([0-9.]+)mm\)", rule)
        if loosened is None:
            continue
        value = float(loosened.group(1))
        if "clearance" in rule and value >= rules.CLEARANCE_MM:
            continue
        if "track_width" in rule and value >= rules.TRACE_WIDTH_MM:
            continue
        names: list[str] = re.findall(
            r"(?:memberOfFootprint|intersectsCourtyard)\('([^']+)'\)", rule
        )
        scopes |= set(names)
        if not re.search(r"memberOfFootprint|intersectsCourtyard", rule):
            scopes.add("<unscoped>")
    return scopes


class DesignRulesTest(unittest.TestCase):
    """The U74-only fine-pitch exception: scoped rule text, mutations, and a DRC run without it."""

    def test_only_u74_gets_the_fine_pitch_exception(self) -> None:
        text = exports.render_design_rules()
        self.assertEqual(exception_scopes(text), {rules.FINE_PITCH_REFERENCE})
        self.assertIn(f"(min {rules.CLEARANCE_MM}mm)", text)
        self.assertIn(f"(min {rules.TRACE_WIDTH_MM}mm)", text)

    def test_an_exception_naming_another_part_is_reported(self) -> None:
        moved = exports.render_design_rules().replace("'U74'", "'U5'")
        self.assertEqual(exception_scopes(moved), {"U5"})
        unscoped = re.sub(
            r'(\(rule "U74 fine-pitch clearance"\n(?:  \(layer "[^"]*"\)\n)?)'
            r'  \(condition "[^"]*"\)\n',
            r"\1",
            exports.render_design_rules(),
        )
        self.assertIn("<unscoped>", exception_scopes(unscoped))

    def test_netclass_keeps_the_board_clearance(self) -> None:
        project = cast(NetSettings, json.loads(exports.render_project()))
        for netclass in project["net_settings"]["classes"]:
            self.assertEqual(netclass["clearance"], rules.CLEARANCE_MM)
            self.assertEqual(netclass["track_width"], rules.TRACE_WIDTH_MM)

    def test_only_escape_copper_touches_u74s_courtyard(self) -> None:
        # S4c r-m2: the exception follows any F.Cu track touching the courtyard, so
        # every such track must end within the escape margin (the router cuts
        # longer ones), and no other layer is covered.
        board = _routed_board()
        box = _escape_box(board, rules.FINE_PITCH_ESCAPE_MARGIN_MM)
        courtyard = _escape_box(board, 0.0)
        long_tracks: list[str] = []
        for track in board.GetTracks():
            if isinstance(track, pcbnew.PCB_VIA) or track.GetLayer() != pcbnew.F_Cu:
                continue
            half = track.GetWidth() // 2
            ends = (track.GetStart(), track.GetEnd())
            if not _segment_touches(ends, _grow(courtyard, half)):
                continue
            if not all(_inside(end, box) for end in ends):
                long_tracks.append(
                    f"{track.GetNetname()} {_mm(ends[0])}-{_mm(ends[1])}"
                )
        self.assertEqual(long_tracks, [])
        self.assertEqual(exports.render_design_rules().count('(layer "F.Cu")'), 2)
