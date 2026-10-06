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

    @unittest.skipIf(shutil.which("kicad-cli") is None, "kicad-cli is required")
    def test_routed_board_needs_the_exception_only_at_u74(self) -> None:
        # DRC with the board-wide rules only: every violation must LIE (its
        # closest point between the two items, or the narrow track itself) inside
        # U74's courtyard plus the escape margin; an item merely starting there
        # does not count (S4c r-m2).
        output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
        board = _routed_board()
        box = _escape_box(board, rules.FINE_PITCH_ESCAPE_MARGIN_MM + 0.01)
        # Keep only the board-wide rules (drop the two U74 rules at the end).
        strict = "(rule ".join(exports.render_design_rules().split("(rule ")[:3])
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in ("chess-board.kicad_pcb", "chess-board.kicad_pro"):
                shutil.copy(output / name, work / name)
            (work / "chess-board.kicad_dru").write_text(strict + "\n")
            report = work / "drc.json"
            subprocess.run(
                (
                    "kicad-cli",
                    "pcb",
                    "drc",
                    "--severity-all",
                    "--format",
                    "json",
                    "-o",
                    str(report),
                    str(work / "chess-board.kicad_pcb"),
                ),
                check=True,
                capture_output=True,
            )
            violations = cast(DrcReport, json.loads(report.read_text()))["violations"]
        relevant = [v for v in violations if v["type"] in {"clearance", "track_width"}]
        self.assertTrue(relevant, "without the exception, U74's own lands must flag")
        shapes = _shapes_by_uuid(board)
        stray = [
            v["description"]
            for v in relevant
            if not all(_inside(p, box) for p in _location(v, shapes))
        ]
        self.assertEqual(stray, [])

    def test_violation_location_is_the_gap_not_the_item_origin(self) -> None:
        # Mutation of the locator: two tracks that start beside U74 but are
        # closest far away must be located far away.
        board = _routed_board()
        box = _escape_box(board, rules.FINE_PITCH_ESCAPE_MARGIN_MM)
        left, top, _right, _bottom = box
        far = pcbnew.FromMM(20.0)
        first = ((pcbnew.VECTOR2I(left, top), pcbnew.VECTOR2I(left - far, top)),)
        second = (
            (
                pcbnew.VECTOR2I(left, top - far),
                pcbnew.VECTOR2I(left - far, top - pcbnew.FromMM(0.2)),
            ),
        )
        points = _closest(first, second)
        self.assertFalse(all(_inside(p, box) for p in points))


Box = tuple[int, int, int, int]
Segment = tuple[pcbnew.VECTOR2I, pcbnew.VECTOR2I]


def _routed_board() -> pcbnew.BOARD:
    """Load the published routed board."""
    output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
    return pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))


def _mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    """A native point as (x, y) mm rounded to 1 um."""
    return (round(pcbnew.ToMM(point.x), 3), round(pcbnew.ToMM(point.y), 3))


def _grow(box: Box, by: int) -> Box:
    """A (left, top, right, bottom) box grown by `by` on every side."""
    left, top, right, bottom = box
    return left - by, top - by, right + by, bottom + by


def _escape_box(board: pcbnew.BOARD, margin_mm: float) -> Box:
    """U74's F.CrtYd rectangle grown by `margin_mm`, in board units."""
    module = board.FindFootprintByReference(rules.FINE_PITCH_REFERENCE)
    assert module is not None
    points = [
        p
        for shape in module.GraphicalItems()
        if shape.GetLayer() == pcbnew.F_CrtYd
        for p in (shape.GetStart(), shape.GetEnd())
    ]
    box = (
        min(p.x for p in points),
        min(p.y for p in points),
        max(p.x for p in points),
        max(p.y for p in points),
    )
    return _grow(box, pcbnew.FromMM(margin_mm))


def _inside(point: pcbnew.VECTOR2I, box: Box) -> bool:
    """True if the point lies inside or on the box."""
    left, top, right, bottom = box
    return left <= point.x <= right and top <= point.y <= bottom


def _segment_touches(segment: Segment, box: Box) -> bool:
    """Whether the segment meets the box (sampled finely enough for a 0.01 mm box)."""
    start, end = segment
    steps = max(1, int(math.hypot(end.x - start.x, end.y - start.y) // 5000))
    return any(
        _inside(
            pcbnew.VECTOR2I(
                round(start.x + (end.x - start.x) * k / steps),
                round(start.y + (end.y - start.y) * k / steps),
            ),
            box,
        )
        for k in range(steps + 1)
    )


Shape = tuple[tuple[Segment, ...], int]


def _shapes_by_uuid(board: pcbnew.BOARD) -> dict[str, Shape]:
    """Each copper item as segments plus a half width: a track's centre line, a
    via's centre (half its pad), a pad's or zone fill's polygon edges (0)."""
    shapes: dict[str, Shape] = {}
    for track in board.GetTracks():
        ends = (
            (track.GetPosition(), track.GetPosition())
            if isinstance(track, pcbnew.PCB_VIA)
            else (track.GetStart(), track.GetEnd())
        )
        shapes[track.m_Uuid.AsString()] = ((ends,), track.GetWidth() // 2)
    for module in board.GetFootprints():
        for pad in module.Pads():
            polygon = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(
                polygon, pcbnew.F_Cu, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE
            )
            shapes[pad.m_Uuid.AsString()] = (_edges(polygon), 0)
    for zone in board.Zones():
        polygon = pcbnew.SHAPE_POLY_SET()
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if zone.IsOnLayer(layer):
                polygon = zone.GetFilledPolysList(layer)
                break
        shapes[zone.m_Uuid.AsString()] = (_edges(polygon), 0)
    return shapes
