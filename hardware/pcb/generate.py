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


def add_footprints(board: pcbnew.BOARD, net_by_name, pad_nets):
    pads = {}
    for item in placement.build():
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(item.reference)
        module.SetValue(item.package)
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
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
            pads[(item.reference, logical)] = pad
    return pads


def add_trace(board, net, start, end, layer=pcbnew.F_Cu, width=0.4) -> None:
    trace = pcbnew.PCB_TRACK(board)
    trace.SetStart(start)
    trace.SetEnd(end)
    trace.SetWidth(pcbnew.FromMM(width))
    trace.SetLayer(layer)
    trace.SetNet(net)
    board.Add(trace)


def _via(board, net, at) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(at)
    via.SetWidth(pcbnew.FromMM(0.9))
    via.SetDrill(pcbnew.FromMM(0.4))
    via.SetNet(net)
    board.Add(via)


def route_led_chain(board, net_by_name, pads) -> None:
    """Route the serpentine clock/data chain with obstacle-aware transitions."""
    origin = pcbnew.FromMM(ORIGIN_X_MM)
    for index, connection in enumerate(sources.netlist()["connections"], 1):
        nodes = [tuple(node) for node in connection["pads"]]
        if len(nodes) != 2 or not all(node in pads and node[0].startswith("U") for node in nodes):
            continue
        if nodes[0][1] not in {"5", "6"} or nodes[1][1] not in {"3", "4"}:
            continue
        name = connection["name"] or f"N${index}"
        net = net_by_name[name]
        start, end = (pads[node].GetPosition() for node in nodes)
        c0, c1 = (pads[node].GetParent().GetPosition() for node in nodes)
        if c0.y == c1.y:
            # Four links per half-board pass the quadrant expanders. Drop those
            # links to the free bottom layer and take a lane between reed rows.
            x0, x1 = sorted((start.x, end.x))
            blocker = next((
                module.GetBoundingBox()
                for module in board.GetFootprints()
                if module.GetReference() in {"U1", "U2", "U3", "U4"}
                and module.GetBoundingBox().GetLeft() <= x1
                and module.GetBoundingBox().GetRight() >= x0
                and module.GetBoundingBox().GetTop() <= start.y <= module.GetBoundingBox().GetBottom()
            ), None)
            if blocker is None:
                add_trace(board, net, start, end)
                continue
            # These eight links share space with through-hole expanders and are
            # left to the general signal router rather than guessed here.
            continue

        # Rank transitions run at the board edge. Clock remains on top; data
        # changes to the bottom so the two transitions cannot cross each other.
        right_side = start.x > origin
        direction = 1 if right_side else -1
        is_clock = nodes[0][1] == "6"
        distance_mm = (3.0 if right_side else 8.0) if is_clock else (2.0 if right_side else 7.0)
        distance = pcbnew.FromMM(distance_mm)
        first = pcbnew.VECTOR2I(start.x + direction * distance, start.y)
        second = pcbnew.VECTOR2I(end.x + direction * distance, end.y)
        if is_clock:
            add_trace(board, net, start, first)
            add_trace(board, net, first, second)
            add_trace(board, net, second, end)
        else:
            add_trace(board, net, start, first)
            add_trace(board, net, second, end)
            _via(board, net, first)
            _via(board, net, second)
            add_trace(board, net, first, second, pcbnew.B_Cu)


def fanout_power(board, net_by_name) -> None:
    """Connect surface-mount power pads to dedicated internal planes."""
    for module in board.GetFootprints():
        centre = module.GetPosition()
        for pad in module.Pads():
            name = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or name not in {"GND", "+5V"}:
                continue
            at = pad.GetPosition()
            dx, dy = at.x - centre.x, at.y - centre.y
            length = max(1, round((dx * dx + dy * dy) ** 0.5))
            distance = pcbnew.FromMM(1.0)
            escaped = pcbnew.VECTOR2I(at.x + dx * distance // length, at.y + dy * distance // length)
            add_trace(board, net_by_name[name], at, escaped)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(escaped)
            via.SetWidth(pcbnew.FromMM(0.9))
            via.SetDrill(pcbnew.FromMM(0.4))
            via.SetNet(net_by_name[name])
            board.Add(via)


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


def add_power_planes(board, net_by_name) -> None:
    envelope = __import__("core.board", fromlist=["Board"]).Board()
    corners = (
        (envelope.x_min + 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_min + 1),
        (envelope.x_max - 1, envelope.y_max - 1),
        (envelope.x_min + 1, envelope.y_max - 1),
    )
    for name, layer in (("GND", pcbnew.In1_Cu), ("+5V", pcbnew.In2_Cu)):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net_by_name[name])
        zone.SetLayer(layer)
        zone.Outline().NewOutline()
        for x, y in corners:
            at = point(x, y)
            zone.Outline().Append(at.x, at.y)
        board.Add(zone)


def build() -> None:
    # KiCad normally generates random item UUIDs. A fixed seed makes the native
    # project and every exported artifact reproducible in CI.
    pcbnew.KIID.SeedGenerator(0x43484553)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    pad_nets, names = connectivity()
    net_by_name = {}
    for code, name in enumerate(sorted(set(names)), 1):
        net = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(net)
        net_by_name[name] = net
    pads = add_footprints(board, net_by_name, pad_nets)
    route_led_chain(board, net_by_name, pads)
    fanout_power(board, net_by_name)
    add_outline(board)
    add_power_planes(board, net_by_name)
    pcbnew.SaveBoard(str(BOARD_PATH), board)

    filled = pcbnew.LoadBoard(str(BOARD_PATH))
    pcbnew.ZONE_FILLER(filled).Fill(filled.Zones())
    temporary = BOARD_PATH.with_suffix(".filled.kicad_pcb")
    pcbnew.SaveBoard(str(temporary), filled)
    temporary.replace(BOARD_PATH)
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    DSN_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(board, str(DSN_PATH)):
        raise RuntimeError("KiCad failed to export the autorouter design")
    print(f"wrote {BOARD_PATH}")
    print(f"wrote {DSN_PATH}")


if __name__ == "__main__":
    build()
