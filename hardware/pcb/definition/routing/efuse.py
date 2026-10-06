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
    board = ctx.board
    _, cy = _centre()
    j4 = footprint(board, ComponentReference.POWER_ENTRY_HEADER)
    fused = next(
        p for p in j4.Pads() if p.GetNumber() == PowerHeaderPin.FUSED_TO_SWITCH
    )
    jx, jy = _shared(fused.GetPosition())
    # IN: two necks, then the DC_FUSED loop north and south back to J4.3.
    for path in _bar_paths(-BAR_X, -1, NORTH_IN_Y, SOUTH_IN_Y):
        _path(ctx, "DC_FUSED", [_at(p) for p in path], NECK_MM)
    for bus_y in (NORTH_IN_Y, SOUTH_IN_Y):
        start = (-BAR_X - 0.7, bus_y)
        _path(ctx, "DC_FUSED", [_at(start), native.point(jx, cy + bus_y)], BUS_MM)
    _path(
        ctx,
        "DC_FUSED",
        [native.point(jx, jy), native.point(jx, cy + NORTH_IN_Y)],
        BUS_MM,
    )
    # OUT: two necks, each into a row of +5V plane vias.
    for path in _bar_paths(BAR_X, 1, NORTH_OUT_Y, SOUTH_OUT_Y):
        _path(ctx, "+5V", [_at(p) for p in path], NECK_MM)
        row_y = path[-1][1]
        _path(ctx, "+5V", [_at(path[-1]), _at((OUT_VIA_X[-1], row_y))], BUS_MM)
        for x in OUT_VIA_X:
            native.add_via(board, ctx.nets_by_name["+5V"], _at((x, row_y)))

    # Bias escapes: 0.20 mm while crossing the courtyard, then to their parts.
    def pad_of(reference: str, net: str) -> pcbnew.VECTOR2I:
        part = footprint(board, reference)
        return next(p for p in part.Pads() if p.GetNetname() == net).GetPosition()

    _path(ctx, "EFUSE_EN", [_at((-PIN_X, 0.7)), _at((-1.6, 0.7))], ESCAPE_MM)
    _path(ctx, "EFUSE_EN", [_at((-1.6, 0.7)), _at(EN_ESCAPE_END)], STUB_MM)
    native.add_via(board, ctx.nets_by_name["EFUSE_EN"], _at(EN_ESCAPE_END))
    _path(ctx, "EFUSE_ITIMER", [_at((PIN_X, 0.7)), _at((TURN_X, 0.7))], ESCAPE_MM)
    _path(
        ctx,
        "EFUSE_ITIMER",
        [_at((TURN_X, 0.7)), pad_of("C143", "EFUSE_ITIMER")],
        STUB_MM,
    )
    # ILM and GND turn toward R3's pads while still inside the courtyard (0.20 mm).
    for net, y in (("EFUSE_ILM", 0.225), ("GND", -0.225)):
        path = [_at((PIN_X, y)), _at((TURN_X, y)), pad_of("R3", net)]
        _path(ctx, net, path, ESCAPE_MM)
    _path(ctx, "EFUSE_DVDT", [_at((PIN_X, -0.7)), _at((TURN_X, -0.7))], ESCAPE_MM)
    _path(
        ctx, "EFUSE_DVDT", [_at((TURN_X, -0.7)), pad_of("C142", "EFUSE_DVDT")], STUB_MM
    )
    # R3's, C142's and C144's GND pads share one via; C143 has its own.
    shared_via, timer_via = (_at(v) for v in GROUND_VIAS)
    _path(ctx, "GND", [pad_of("R3", "GND"), pad_of("C142", "GND"), shared_via], STUB_MM)
    _path(ctx, "GND", [pad_of("C143", "GND"), timer_via], STUB_MM)
    # C144's GND pad (S4c) sits beside C142's and shares its via.
    _path(ctx, "GND", [pad_of(OVLO_FILTER, "GND"), pad_of("C142", "GND")], STUB_MM)
    for via in (shared_via, timer_via):
        native.add_via(board, ctx.nets_by_name["GND"], via)
    # OVLO to R4 (its east pad); PGTH joins the OVLO escape.
    r4 = footprint(board, "R4")
    ovlo_pad = next(p for p in r4.Pads() if p.GetNet().GetNetname() == "EFUSE_OVLO")
    junction = (-2.0, 0.225)
    _path(ctx, "EFUSE_OVLO", [_at((-PIN_X, 0.225)), _at(junction)], ESCAPE_MM)
    # R5 is reached from a via on this run (the router finishes it).
    via = _ovlo_via(board)
    _path(ctx, "EFUSE_OVLO", [_at(junction), via, ovlo_pad.GetPosition()], STUB_MM)
    native.add_via(board, ctx.nets_by_name["EFUSE_OVLO"], via)
    _path(ctx, "EFUSE_OVLO", [_at((-PIN_X, -0.7)), _at((-1.5, -0.7))], ESCAPE_MM)
    _path(ctx, "EFUSE_OVLO", [_at((-1.5, -0.7)), _at(junction)], STUB_MM)
    # DC_FUSED stubs: R4 and C141 to the loop, D1 to J4.3's column.
    for reference, bus_y, width in (
        ("R4", SOUTH_IN_Y, STUB_MM),
        ("C141", NORTH_IN_Y, STUB_MM),
    ):
        part = footprint(board, reference)
        pad = next(p for p in part.Pads() if p.GetNetname() == "DC_FUSED")
        x, _ = _shared(pad.GetPosition())
        _path(ctx, "DC_FUSED", [pad.GetPosition(), native.point(x, cy + bus_y)], width)
    tvs = footprint(board, ComponentReference.INPUT_TVS)
    pad = next(p for p in tvs.Pads() if p.GetNetname() == "DC_FUSED")
    _, y = _shared(pad.GetPosition())
    _path(ctx, "DC_FUSED", [pad.GetPosition(), native.point(jx, y)], FAULT_STUB_MM)


def _ovlo_via(board: pcbnew.BOARD) -> pcbnew.VECTOR2I:
    """A via on the U74-to-R4 OVLO run, halfway along it."""
    r4 = footprint(board, "R4")
    pad = next(p for p in r4.Pads() if p.GetNetname() == "EFUSE_OVLO")
    start, end = _at((-2.0, 0.225)), pad.GetPosition()
    return pcbnew.VECTOR2I((start.x + end.x) // 2, (start.y + end.y) // 2)


def _r5_escape(ctx: RoutingContext) -> pcbnew.VECTOR2I:
    """R5's OVLO pad leaves by a fixed via above it, between R5 and R6 (C144 takes
    the side where a router escape would go, S4c)."""
    pad = next(
        p for p in footprint(ctx.board, "R5").Pads() if p.GetNetname() == "EFUSE_OVLO"
    )
    x, y = _shared(pad.GetPosition())
    via = native.point(x, y + R5_ESCAPE_MM)
    _path(ctx, "EFUSE_OVLO", [pad.GetPosition(), via], STUB_MM)
    native.add_via(ctx.board, ctx.nets_by_name["EFUSE_OVLO"], via)
    return via


def route_efuse_bias(ctx: RoutingContext) -> None:
    """Grid-route EN, OVLO and RUN (B.Cu preferred) between vias, never into a pad.

    Every escape via of all three nets is placed before any of them is routed,
    so no route can pass where another net's via will stand.
    """
    plans: list[
        tuple[str, list[Endpoint[str]], dict[Endpoint[str], pcbnew.VECTOR2I]]
    ] = []
    for net in ("EFUSE_EN", "EFUSE_OVLO", "RUN"):
        nodes: list[Endpoint[str]] = []
        points: dict[Endpoint[str], pcbnew.VECTOR2I] = {}
        for node in ctx.endpoints_by_net[net]:
            reference = node.reference
            if net == "EFUSE_OVLO" and reference == EFUSE:
                continue  # Joined to R4 by fixed copper.
            if net == "RUN" and reference == "R8":
                continue  # Joined to R6 by fixed copper.
            if net == "EFUSE_OVLO" and reference == OVLO_FILTER:
                continue  # Joined to R5 by fixed copper.
            nodes.append(node)
            if reference == EFUSE:
                points[node] = _at(EN_ESCAPE_END)
            elif net == "EFUSE_OVLO" and reference == "R4":
                points[node] = _ovlo_via(ctx.board)
            elif net == "EFUSE_OVLO" and reference == "R5":
                points[node] = _r5_escape(ctx)
            elif reference == ComponentReference.POWER_ENTRY_HEADER:
                points[node] = ctx.pads_by_endpoint[node].GetPosition()
            else:
                points[node] = escape_endpoint(ctx, net, node, add_via=True)
        # Start from the escape via (B.Cu preferred); J4's plated pad, which
        # takes either layer, is reached last.
        nodes.sort(
            key=lambda node: node.reference == ComponentReference.POWER_ENTRY_HEADER
        )
        plans.append((net, nodes, points))
    # R8 (wetting load) sits under R6: one short F.Cu run joins their RUN pads.
    run = [
        next(p for p in footprint(ctx.board, ref).Pads() if p.GetNetname() == "RUN")
        for ref in ("R6", "R8")
    ]
    _path(ctx, "RUN", [pad.GetPosition() for pad in run], STUB_MM)
    # C144 (OVLO filter, S4c) sits beside R5: one short F.Cu run joins their pads.
    ovlo = [
        next(
            p
            for p in footprint(ctx.board, ref).Pads()
            if p.GetNetname() == "EFUSE_OVLO"
        )
        for ref in ("R5", OVLO_FILTER)
    ]
    _path(ctx, "EFUSE_OVLO", [pad.GetPosition() for pad in ovlo], STUB_MM)
    # No router via within 1.2 mm of a bias pad or escape via: a via that close
    # breaks the hole spacing or the pad's mask dam.
    keep: set[tuple[int, int]] = set()
    reach = 1.2
    for _net, nodes, points in plans:
        spots = [
            *points.values(),
            *(ctx.pads_by_endpoint[n].GetPosition() for n in nodes),
        ]
        for spot in spots:
            x, y = pcbnew.ToMM(spot.x), pcbnew.ToMM(spot.y)
            span = range(-math.ceil(reach / GRID_MM), math.ceil(reach / GRID_MM) + 1)
            keep.update(
                (round(x / GRID_MM) + i, round(y / GRID_MM) + j)
                for i in span
                for j in span
                if math.hypot(i * GRID_MM, j * GRID_MM) <= reach
            )
    ctx = replace(ctx, host_header_via_keepouts=ctx.host_header_via_keepouts | keep)
    for net, nodes, points in plans:
        route_tree(
            ctx,
            net,
            nodes,
            points,
            allow_vias=True,
            preferred_layer_index=1,
            label_errors=True,
        )
