"""J1 pad n lies under Pi header pin n, seen from the PCB top (no mirror error).

The Pi Zero 2 W hangs component side up below the board (RP-008358-DS-1 drawing,
transform in shared/dimensions/case.py). Its male header plugs up into J1 on the
PCB bottom, so each J1 hole must sit exactly at `pi_header_pin_xy(n)`. A plain
KiCad flip of a top-view footprint mirrors it; the negative case proves this test
catches that.
"""

import unittest

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from shared import dimensions

TOLERANCE_NM = 10_000  # 0.01 mm


def header_mismatches(footprint: pcbnew.FOOTPRINT) -> list[int]:
    """Pin numbers whose pad is not where the Pi's pin of that number lands."""
    wrong: list[int] = []
    for pad in footprint.Pads():
        number = int(pad.GetNumber())
        expected = native.point(*dimensions.pi_header_pin_xy(number))
        at = pad.GetPosition()
        if (
            abs(at.x - expected.x) > TOLERANCE_NM
            or abs(at.y - expected.y) > TOLERANCE_NM
        ):
            wrong.append(number)
    return sorted(wrong)
