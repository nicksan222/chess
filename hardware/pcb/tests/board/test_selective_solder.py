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
