"""Bottom-side parts stay out of the case ledge, the bosses and the panel volumes.

The case (shared/dimensions/case.py, interface S3a M1-M5) supports the board on a
perimeter ledge (PCB_BOTTOM_EDGE_KEEPOUT_MM from the outline), on Ø7 bosses at
PCB_SUPPORT_POSITIONS_MM (keep 1.0 mm beyond the boss radius), and reserves
BOTTOM_SIDE_KEEPOUTS_MM below the board for the rear-wall jack and rocker.
"""

import math
import unittest
from dataclasses import replace
from typing import ClassVar

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.parts.part import DrawingView
from shared import dimensions

BOSS_KEEP_MM = dimensions.PCB_SUPPORT_BOSS_DIAMETER_MM / 2 + 1.0
EXPECTED_BOTTOM = frozenset({"J1", "J4", "C1", "C140"})

Box = tuple[float, float, float, float]
Point = tuple[float, float]


def _relative(footprint: pcbnew.FOOTPRINT, at: pcbnew.VECTOR2I) -> Point:
    """Offset from the footprint origin in mm, Y up, seen from the board top."""
    origin = footprint.GetPosition()
    return (pcbnew.ToMM(at.x - origin.x), pcbnew.ToMM(origin.y - at.y))
