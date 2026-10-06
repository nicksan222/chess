"""Polarity silkscreen and solder-mask webs measured on the native boards.

Polarity pads are typed here from the datasheets cited in `test_land_patterns.py`:
pin 1 of every IC, LED, Hall sensor and connector, the TVS cathode (colour band) and
the electrolytic "+" lead. Clearances use the fabricator minimums in `rules`.
"""

import math
import os
import unittest
from collections import defaultdict
from pathlib import Path
from typing import ClassVar

import pcbnew

from pcb.definition import board, native, rules

PCB_ROOT = Path(__file__).resolve().parents[2]

POLARITY_PADS = {
    "SK9822": "1",
    "TCA9554": "1",
    "AHCT125": "1",
    "HALL_SENSOR": "1",
    "EFUSE": "1",
    "CAP_560U": "1",
    "POWER_HEADER": "1",
    "PI_ZERO_HEADER": "1",
    "OLED_HEADER": "1",
}

# A mark this close to the polarity pad's copper reads as belonging to it.
MARK_REACH_MM = 1.0

GRID_MM = 5.0

Box = tuple[float, float, float, float]
# A rounded rectangle: (left, top, right, bottom, corner radius), in mm.
Shape = tuple[float, float, float, float, float]


def _rounded(pad: pcbnew.PAD, margin: float) -> Shape:
    """Pad copper grown by `margin`: round/oval pads keep their full rounding."""
    box = pad.GetBoundingBox()
    size = pad.GetSize()
    round_pad = pad.GetShape() in (pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL)
    corner = pcbnew.ToMM(min(size.x, size.y)) / 2 if round_pad else 0.0
    return (
        pcbnew.ToMM(box.GetLeft()) - margin,
        pcbnew.ToMM(box.GetTop()) - margin,
        pcbnew.ToMM(box.GetRight()) + margin,
        pcbnew.ToMM(box.GetBottom()) + margin,
        corner + margin,
    )


def _mask_opening(pad: pcbnew.PAD, board_margin: int) -> Shape:
    """Pad copper grown by its (else the board's) solder-mask expansion."""
    local = pad.GetLocalSolderMaskMargin()
    return _rounded(
        pad, max(pcbnew.ToMM(board_margin if local is None else local), 0.0)
    )
