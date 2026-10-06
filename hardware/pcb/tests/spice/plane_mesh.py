"""Resistive mesh of the +5V, GND and LED_5V planes built from the routed board.

Each plane is a square grid of sheet-resistance resistors: R□ = ρ / t, with ρ the
annealed-copper resistivity (IEC 60028: 1.7241e-8 Ω·m at 20 °C) and t the inner
copper weight in manufacturing.json (1 oz = 0.035 mm). Clearance holes are not drawn
individually: R□ is scaled by outline area / filled area of that plane's actual
zone fill, so the mesh is a smeared approximation, not a field solution. Supply
enters through the measured thermal spokes of the net-derived plane-entry pads; every LED and the Pi header draw their load from
the nodes under their own supply and ground pads. Since S6 the LEDs sit on the
LED_5V plane (In6), joined to the +5V plane only through the LED switch Q1: its
source and drain vias (barrel resistance each) and its on-resistance.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pcbnew

from spice.circuit import SpiceCircuit

PCB_ROOT = Path(__file__).resolve().parents[2]

COPPER_RESISTIVITY_OHM_M = 1.7241e-8
OZ_MM = 0.035
MESH_PITCH_MM = 5.0

SUPPLY_NETS = frozenset({"DC_IN", "DC_FUSED"})
# Contacts that open when the supply is connected (a jack's shunt) carry no supply
# current: (part key, pad). None is on the board since S3a; kept by role.
SWITCHED_CONTACTS = frozenset({("BARREL_JACK", "SLEEVE SHUNT")})
# Pads on a supply part that only carry its bias current (TPS25947 GND, IQ 0.6 mA).
BIAS_ONLY = frozenset({("EFUSE", "8")})
# Plated via barrel: board thickness through IPC-6012 Class 2 wall (ampacity test).
VIA_WALL_MM = 0.018  # PCBWay standard floor (S4c, as tests/board/test_ampacity.py)
BOARD_THICKNESS_MM = 1.6
PLANE_LAYERS = {"+5V": pcbnew.In2_Cu, "GND": pcbnew.In1_Cu, "LED_5V": pcbnew.In6_Cu}
LED_SWITCH = "Q1"
SWITCH_SOURCE_PADS = ("1", "2", "3")
SWITCH_DRAIN_PADS = ("5", "6", "7", "8")


@dataclass(frozen=True)
class Load:
    """A current sink between two plane points: a part's supply pad and ground pad, and its current."""

    name: str
    supply: pcbnew.VECTOR2I
    ground: pcbnew.VECTOR2I
    amps: float


def routed_board() -> pcbnew.BOARD:
    """The published routed board (from `PCB_OUTPUT` when set, else `generated/`)."""
    output = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
    return pcbnew.LoadBoard(str(output / "chess-board.kicad_pcb"))


def _inner_copper_mm() -> float:
    """Inner-layer copper thickness (mm) from `manufacturing.json`: 1 oz thickness x the minimum ounces."""
    record = cast(
        dict[str, dict[str, float]],
        json.loads((PCB_ROOT / "definition/manufacturing.json").read_text()),
    )
    return OZ_MM * record["fabrication"]["inner_copper_oz_min"]


def power_entry_pads(board: pcbnew.BOARD) -> list[pcbnew.PAD]:
    """Every pad (plated or via-fed) that hands the off-board supply to a plane.

    Derived from nets: a part with a pad on DC_IN/DC_FUSED brings the supply on
    board; its +5V and GND pads are where that current enters the planes, except
    contacts that open when the supply is plugged in and bias-only pins. Two-pad
    parts on a supply net are shunts (bypass caps, the TVS) and pass no supply
    current. A connector or eFuse change therefore cannot drop an entry silently.
    """
    entries: list[pcbnew.PAD] = []
    for footprint in board.GetFootprints():
        pads = list(footprint.Pads())
        if len(pads) <= 2 or not any(p.GetNetname() in SUPPLY_NETS for p in pads):
            continue
        key = (
            footprint.GetFieldText("PartKey")
            if footprint.HasFieldByName("PartKey")
            else ""
        )
        entries.extend(
            p
            for p in pads
            if p.GetNetname() in PLANE_LAYERS
            and (key, p.GetNumber()) not in SWITCHED_CONTACTS | BIAS_ONLY
        )
    return entries


def _on(point: pcbnew.VECTOR2I, track: pcbnew.PCB_TRACK) -> bool:
    """True if `point` lies on the track segment (within 1 um)."""
    a, b = track.GetStart(), track.GetEnd()
    dx, dy = b.x - a.x, b.y - a.y
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else ((point.x - a.x) * dx + (point.y - a.y) * dy) / length
    t = min(max(t, 0.0), 1.0)
    return math.hypot(a.x + t * dx - point.x, a.y + t * dy - point.y) <= 1000


def tracks_touching(board: pcbnew.BOARD, pad: pcbnew.PAD) -> list[pcbnew.PCB_TRACK]:
    """Same-net tracks with an end inside the pad's bounding box: how a pad's copper joins the plane."""
    box = pad.GetBoundingBox()
    return [
        track
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA)
        and track.GetNetCode() == pad.GetNetCode()
        and any(
            box.GetLeft() <= end.x <= box.GetRight()
            and box.GetTop() <= end.y <= box.GetBottom()
            for end in (track.GetStart(), track.GetEnd())
        )
    ]


def connected_vias(board: pcbnew.BOARD, pad: pcbnew.PAD) -> list[pcbnew.PCB_VIA]:
    """Vias on the copper reached from the pad through touching segments."""
    tracks = [
        t
        for t in board.GetTracks()
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == pad.GetNetCode()
    ]
    reached = tracks_touching(board, pad)
    frontier = list(reached)
    while frontier:
        current = frontier.pop()
        for other in tracks:
            if other in reached:
                continue
            ends = (other.GetStart(), other.GetEnd())
            mine = (current.GetStart(), current.GetEnd())
            if any(_on(e, current) for e in ends) or any(_on(e, other) for e in mine):
                reached.append(other)
                frontier.append(other)
    return [
        v
        for v in board.GetTracks()
        if isinstance(v, pcbnew.PCB_VIA)
        and v.GetNetCode() == pad.GetNetCode()
        and any(_on(v.GetPosition(), t) for t in reached)
    ]


def spoke_width_mm(board: pcbnew.BOARD, pad: pcbnew.PAD, layer: int) -> float:
    """Copper crossing the middle of the pad's thermal gap on a plane layer."""
    zone = next(
        z
        for z in board.Zones()
        if z.GetLayer() == layer and z.GetNetCode() == pad.GetNetCode()
    )
    middle = zone.GetThermalReliefGap() // 2
    band = pcbnew.FromMM(0.05)
    outer = pcbnew.SHAPE_POLY_SET()
    inner = pcbnew.SHAPE_POLY_SET()
    error = pcbnew.FromMM(0.005)
    pad.TransformShapeToPolygon(outer, layer, middle + band, error, pcbnew.ERROR_INSIDE)
    pad.TransformShapeToPolygon(inner, layer, middle - band, error, pcbnew.ERROR_INSIDE)
    outer.BooleanSubtract(inner)
    copper = pcbnew.SHAPE_POLY_SET(zone.GetFilledPolysList(layer))
    copper.BooleanIntersection(outer)
    return copper.Area() / 1e12 / pcbnew.ToMM(2 * band)


def thermal_gap_mm(board: pcbnew.BOARD, layer: int, netcode: int) -> float:
    """Thermal-relief gap (mm) of the zone on `layer` for `netcode`, for the series spoke resistance."""
    zone = next(
        z for z in board.Zones() if z.GetLayer() == layer and z.GetNetCode() == netcode
    )
    return pcbnew.ToMM(zone.GetThermalReliefGap())


class PlaneMesh:
    """Two plane meshes sharing grid geometry; node names p_i_j and g_i_j."""

    def __init__(self, board: pcbnew.BOARD) -> None:
        self.board = board
        zones = {zone.GetNetname(): zone for zone in board.Zones()}
        self.zones = (zones["+5V"], zones["GND"], zones["LED_5V"])
        box = zones["+5V"].GetBoundingBox()
        self.left, self.top = box.GetLeft(), box.GetTop()
        pitch = pcbnew.FromMM(MESH_PITCH_MM)
        self.pitch = pitch
        self.columns = (box.GetRight() - box.GetLeft()) // pitch + 1
        self.rows = (box.GetBottom() - box.GetTop()) // pitch + 1
        thickness = _inner_copper_mm() / 1000
        self.sheet_ohms = COPPER_RESISTIVITY_OHM_M / thickness

    def node(self, prefix: str, at: pcbnew.VECTOR2I) -> str:
        """Mesh node name for the grid cell nearest `at`, clamped to the mesh."""
        column = min(max(round((at.x - self.left) / self.pitch), 0), self.columns - 1)
        row = min(max(round((at.y - self.top) / self.pitch), 0), self.rows - 1)
        return f"{prefix}_{column}_{row}"

    def _fill_ratio(self, zone: pcbnew.ZONE) -> float:
        """Filled area over outline area of the zone: how much of the sheet is really copper."""
        filled = zone.GetFilledPolysList(zone.GetLayer()).Area()
        outline = zone.Outline().Area()
        return filled / outline
