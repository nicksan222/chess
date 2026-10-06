"""Bottom-mounted THT parts can be selectively soldered from the top (S4c).

J1, J4, C1 and C140 sit on the bottom, so their joints are made on the top side
among the SMD parts. A selective-solder nozzle needs a keep-out around each joint
(manufacturing review: 3-5 mm typical, not yet confirmed for PCBWay): every plated
through-hole pad of a bottom-side footprint keeps at least 3 mm from any top-side
part's courtyard, which bounds its body as well as its pads (reviewer m5), and from
any top-side SMD pad. Bounding boxes are used, which under-estimate the true gap,
so the check is conservative.
"""

import math
import os
import unittest
from pathlib import Path

import pcbnew

PCB_ROOT = Path(__file__).resolve().parents[2]
Box = tuple[int, int, int, int]
NOZZLE_KEEPOUT_MM = 3.0


def _gap_mm(first: pcbnew.PAD, second: pcbnew.PAD) -> float:
    """Edge-to-edge distance (mm) between two pads' bounding boxes, 0 if they touch."""
    a, b = first.GetBoundingBox(), second.GetBoundingBox()
    dx = max(b.GetLeft() - a.GetRight(), a.GetLeft() - b.GetRight(), 0)
    dy = max(b.GetTop() - a.GetBottom(), a.GetTop() - b.GetBottom(), 0)
    return pcbnew.ToMM(round(math.hypot(dx, dy)))


def _box_gap_mm(first: pcbnew.BOX2I, second: Box) -> float:
    """Distance (mm) from a bounding box to a (left, top, right, bottom) box."""
    left, top, right, bottom = second
    dx = max(left - first.GetRight(), first.GetLeft() - right, 0)
    dy = max(top - first.GetBottom(), first.GetTop() - bottom, 0)
    return pcbnew.ToMM(round(math.hypot(dx, dy)))


def top_courtyards(board: pcbnew.BOARD) -> list[tuple[str, Box]]:
    """Each top-side footprint's F.CrtYd rectangle (left, top, right, bottom)."""
    found: list[tuple[str, Box]] = []
    for module in board.GetFootprints():
        if module.IsFlipped():
            continue
        points = [
            p
            for shape in module.GraphicalItems()
            if shape.GetLayer() == pcbnew.F_CrtYd
            for p in (shape.GetStart(), shape.GetEnd())
        ]
        if points:
            found.append(
                (
                    module.GetReference(),
                    (
                        min(p.x for p in points),
                        min(p.y for p in points),
                        max(p.x for p in points),
                        max(p.y for p in points),
                    ),
                )
            )
    return found


def crowded_courtyards(board: pcbnew.BOARD, keepout_mm: float) -> list[str]:
    """Bottom-side through-hole joints that come within `keepout_mm` of a top-side courtyard."""
    courtyards = top_courtyards(board)
    findings: list[str] = []
    for module in board.GetFootprints():
        if not module.IsFlipped():
            continue
        for joint in module.Pads():
            if joint.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
            for reference, box in courtyards:
                gap = _box_gap_mm(joint.GetBoundingBox(), box)
                if gap < keepout_mm:
                    findings.append(
                        f"{module.GetReference()}-{joint.GetNumber()} is {gap:.2f} mm "
                        f"from {reference}'s courtyard"
                    )
    return findings


def crowded_joints(board: pcbnew.BOARD, keepout_mm: float) -> list[str]:
    """Bottom-side through-hole joints that come within `keepout_mm` of a top-side SMD pad."""
    smd = [
        (module.GetReference(), pad)
        for module in board.GetFootprints()
        if not module.IsFlipped()
        for pad in module.Pads()
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
    ]
    findings: list[str] = []
    for module in board.GetFootprints():
        if not module.IsFlipped():
            continue
        for joint in module.Pads():
            if joint.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
            for reference, pad in smd:
                gap = _gap_mm(joint, pad)
                if gap < keepout_mm:
                    findings.append(
                        f"{module.GetReference()}-{joint.GetNumber()} is {gap:.2f} mm "
                        f"from {reference}-{pad.GetNumber()}"
                    )
    return findings
