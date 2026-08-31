#!/usr/bin/env python3
"""Compose the KiCad PCB from shared contracts and reviewed connectivity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pcbnew

PCB_ROOT = Path(__file__).resolve().parent
HARDWARE_ROOT = PCB_ROOT.parent
sys.path.insert(0, str(PCB_ROOT))
sys.path.insert(0, str(HARDWARE_ROOT))

import footprints  # noqa: E402
from footprints import base as footprint_base  # noqa: E402
from core import placement, sources  # noqa: E402

BOARD_PATH = PCB_ROOT / "chess-board.kicad_pcb"
PROJECT_PATH = PCB_ROOT / "chess-board.kicad_pro"
DSN_PATH = PCB_ROOT / "generated" / "chess-board.dsn"
ORIGIN_X_MM = 200.0
ORIGIN_Y_MM = 220.0


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x + ORIGIN_X_MM), pcbnew.FromMM(ORIGIN_Y_MM - y))


def connectivity() -> tuple[dict[tuple[str, str], str], list[str]]:
    pad_nets: dict[tuple[str, str], str] = {}
    names: list[str] = []
    for index, connection in enumerate(sources.netlist()["connections"], 1):
        pads = [tuple(pad) for pad in connection["pads"]]
        name = connection["name"] or f"N${index}"
        names.append(name)
        for pad in pads:
            if pad in pad_nets:
                raise RuntimeError(f"{pad} belongs to multiple connectivity groups")
            pad_nets[pad] = name
    return pad_nets, names


def add_footprints(board: pcbnew.BOARD, net_by_name, pad_nets) -> None:
    for item in placement.build():
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(item.reference)
        module.SetValue(item.package)
        module.SetPosition(point(item.x, item.y))
        board.Add(module)
        for logical, number, (x, y), definition in item.pads():
            pad = pcbnew.PAD(module)
            pad.SetNumber(number)
            pad.SetPosition(point(x, y))
            pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(definition.width), pcbnew.FromMM(definition.height)))
            pad.SetShape({
                footprint_base.ROUND: pcbnew.PAD_SHAPE_CIRCLE,
                footprint_base.RECT: pcbnew.PAD_SHAPE_RECT,
                footprint_base.OBLONG: pcbnew.PAD_SHAPE_OVAL,
            }[definition.shape])
            if definition.plated_through:
                pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
                pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(definition.drill), pcbnew.FromMM(definition.drill)))
                pad.SetLayerSet(pad.PTHMask())
            else:
                pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                pad.SetLayerSet(pad.SMDMask())
            name = pad_nets.get((item.reference, logical))
            if name:
                pad.SetNet(net_by_name[name])
            module.Add(pad)


def add_outline(board: pcbnew.BOARD) -> None:
    dimensions = sources.dimensions()
    width, height, _thickness = dimensions.PCB_SIZE_MM
    x0, x1 = -width / 2, width / 2
    y1 = dimensions.PLAYING_SPAN_MM / 2
    y0 = y1 - height
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    for index, start in enumerate(corners):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(point(*start))
        edge.SetEnd(point(*corners[(index + 1) % 4]))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)


def build() -> None:
    board = pcbnew.BOARD()
    pad_nets, names = connectivity()
    net_by_name = {}
    for code, name in enumerate(sorted(set(names)), 1):
        net = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(net)
        net_by_name[name] = net
    add_footprints(board, net_by_name, pad_nets)
    add_outline(board)
    pcbnew.SaveBoard(str(BOARD_PATH), board)
    DSN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(board, str(DSN_PATH)):
        raise RuntimeError("KiCad failed to export the autorouter design")
    print(f"wrote {BOARD_PATH}")
    print(f"wrote {DSN_PATH}")


if __name__ == "__main__":
    build()
