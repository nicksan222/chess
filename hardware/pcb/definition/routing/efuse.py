"""Fixed copper around the U74 eFuse (S4b), laid before any grid-routed net.

The RPW0010A IN (5) and OUT (6) bars can only be reached at their two ends, through
a channel between the corner legs (TI SLVSFC9C p73). Each bar is therefore fed at
both ends by a 0.35 mm neck (two necks in parallel carry the 2 A rating,
tests/board/test_ampacity.py): IN from a DC_FUSED loop that starts at J4.3, OUT to
two rows of +5V plane vias. The 0.45 mm-pitch bias pins leave by 0.20 mm escapes
(the lead-approved U74-only DRC rule, `output/exports.py`) to points from which the
grid router finishes EN, OVLO (R4 to R5) and RUN. PGTH shares the OVLO node.
Coordinates are offsets from U74's placement in shared mm (Y up), U74 at 0 degrees.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace
from itertools import pairwise

import pcbnew

from pcb.definition import native, rules
from pcb.definition.routing.paths import GRID_MM
from pcb.definition.routing.policies import (
    RoutingContext,
    escape_endpoint,
    footprint,
    route_tree,
)
from shared import dimensions
from shared.electronics import ComponentReference, PowerHeaderPin
from shared.electronics.base import Endpoint

# Width of the narrow necks that feed each IN/OUT bar (two in parallel are checked to carry
# the 2 A rating by `tests/board/test_ampacity.py`).
NECK_MM = 0.35
# Where the right-column escapes leave their 0.20 mm run (inside the courtyard).
TURN_X = 1.4
# Width of the bias escapes while they cross the courtyard (the scoped U74 DRC exception).
ESCAPE_MM = 0.20
STUB_MM = rules.TRACE_WIDTH_MM
FAULT_STUB_MM = 1.0
BUS_MM = rules.POWER_TRACE_WIDTH_MM
# Reference of the eFuse (U74), resolved through the shared reference enum.
EFUSE = ComponentReference.INPUT_EFUSE

# Shared-mm offsets from the U74 centre. The necks run 0.01 mm outside the bar
# centres so the IN and OUT necks clear each other by the 0.16 mm U74 rule (S4c).
BAR_X = 0.26
PIN_X = 0.9
NORTH_IN_Y = 3.1
# The south loop's 1.5 mm copper stays off U74's courtyard (S4c r-m2).
SOUTH_IN_Y = -2.22
NORTH_OUT_Y = 3.9
SOUTH_OUT_Y = -3.9
OUT_VIA_X = (1.65, 2.85, 4.05)
# Router start point for EN (escape end); the other bias parts sit at the pins.
EN_ESCAPE_END = (-2.4, 1.5)
# GND vias: R3, C142 and C144 share one, C143 has its own.
GROUND_VIAS = ((4.5, -2.2), (5.45, 2.4))

Point = tuple[float, float]

OVLO_FILTER = "C144"
# R5 to its OVLO escape via (midway to R6, clear of both pads' mask).
R5_ESCAPE_MM = 1.3


def _centre() -> Point:
    """U74's placement centre in shared mm (from the shared placement table)."""
    return dimensions.PCB_STRIP_PLACEMENTS[EFUSE].centre_mm


def _at(offset: Point) -> pcbnew.VECTOR2I:
    """Native point for an offset (shared mm, Y up) from U74's centre; all offsets below use this."""
    cx, cy = _centre()
    return native.point(cx + offset[0], cy + offset[1])


def _shared(at: pcbnew.VECTOR2I) -> Point:
    """Inverse of `native.point`: a native position back to shared (centre-origin, Y up) mm."""
    return (
        pcbnew.ToMM(at.x) - native.ORIGIN_X_MM,
        native.ORIGIN_Y_MM - pcbnew.ToMM(at.y),
    )


def _path(
    ctx: RoutingContext, net: str, points: Sequence[pcbnew.VECTOR2I], width: float
) -> None:
    """Lay a polyline of straight tracks of one `width` on net `net` (F.Cu)."""
    for start, end in pairwise(points):
        native.add_trace(ctx.board, ctx.nets_by_name[net], start, end, width=width)


def _bar_paths(
    x: float, sign: int, north_y: float, south_y: float
) -> list[list[Point]]:
    """Necks from both bar ends, turning away (sign) from the other bar, to a row."""
    paths: list[list[Point]] = []
    for end, row_y in ((1, north_y), (-1, south_y)):
        path = [(x, end * 1.05), (x, end * 1.4), (x + sign * 0.7, end * 2.1)]
        if abs(row_y - end * 2.1) > 1e-6:
            path.append((x + sign * 0.7, row_y))
        paths.append(path)
    return paths


def route_efuse_power(ctx: RoutingContext) -> None:
    """Fixed copper for the eFuse power path and its bias escapes, laid before grid routing.

    IN: two necks into a DC_FUSED loop that returns to J4.3. OUT: two necks into two rows of +5V
    vias. Then the 0.20 mm bias escapes for EN, ITIMER, ILM, GND, DVDT and OVLO, the shared GND
    vias, and the DC_FUSED stubs for R4, C141 and D1. Positions are fixed offsets from U74 because
    the pad gaps are too tight for the grid router.
    """
