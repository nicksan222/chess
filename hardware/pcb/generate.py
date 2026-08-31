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
from core import grid_router, placement, rules, sources  # noqa: E402
from core.nets import ButtonNet, Net  # noqa: E402
from shared.components import COMPONENTS  # noqa: E402

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
    physical_numbers = {
        (item.reference, logical): number
        for item in placement.build()
        for logical, number, _position, _definition in item.pads()
    }
    for index, connection in enumerate(sources.netlist()["connections"], 1):
        pads = [tuple(pad) for pad in connection["pads"]]
        if connection.get("no_connect"):
            if len(pads) != 1:
                raise RuntimeError("a no-connect group must contain exactly one pad")
            reference, logical = pads[0]
            physical = physical_numbers[(reference, logical)]
            name = f"unconnected-({reference}-Pad{physical})"
        else:
            name = connection["name"] or f"N${index}"
        names.append(name)
        for pad in pads:
            if pad in pad_nets:
                raise RuntimeError(f"{pad} belongs to multiple connectivity groups")
            pad_nets[pad] = name
    return pad_nets, names


def add_footprints(board: pcbnew.BOARD, net_by_name, pad_nets):
    pads = {}
    components = sources.netlist()["components"]
    for item in placement.build():
        entry = components[item.reference]
        spec = COMPONENTS[entry["part_key"]]
        if spec.package != item.package:
            raise RuntimeError(
                f"{item.reference}: {spec.mpn} requires {spec.package!r}, "
                f"not {item.package!r}"
            )
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(item.reference)
        module.SetValue(spec.mpn)
        module.SetLibDescription(f"{spec.manufacturer} {spec.mpn}: {spec.description}")
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(point(item.x, item.y))
        board.Add(module)
        width, height = item.footprint.courtyard_at(item.rotation)
        for layer, inset in ((pcbnew.F_CrtYd, 0.0), (pcbnew.F_Fab, 0.25)):
            x0, x1 = item.x - width / 2 + inset, item.x + width / 2 - inset
            y0, y1 = item.y - height / 2 + inset, item.y + height / 2 - inset
            corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            for index, start in enumerate(corners):
                line = pcbnew.PCB_SHAPE(module)
                line.SetShape(pcbnew.SHAPE_T_SEGMENT)
                line.SetStart(point(*start))
                line.SetEnd(point(*corners[(index + 1) % 4]))
                line.SetLayer(layer)
                line.SetWidth(pcbnew.FromMM(0.05 if layer == pcbnew.F_CrtYd else 0.1))
                module.Add(line)
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
    via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
    via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
    via.SetNet(net)
    board.Add(via)


def route_led_chain(board, net_by_name, pads, *, obstructed_only=False) -> None:
    """Route regular links first and expander-obstructed links after sensors."""
    origin = pcbnew.FromMM(ORIGIN_X_MM)
    for index, connection in enumerate(sources.netlist()["connections"], 1):
        nodes = [tuple(node) for node in connection["pads"]]
        if len(nodes) != 2 or not all(node in pads and node[0].startswith("U") for node in nodes):
            continue
        if nodes[0][1] in {"3", "4"} and nodes[1][1] in {"5", "6"}:
            nodes.reverse()
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
                if module.GetReference() not in {nodes[0][0], nodes[1][0]}
                and module.GetBoundingBox().GetLeft() <= x1
                and module.GetBoundingBox().GetRight() >= x0
                and module.GetBoundingBox().GetTop() <= start.y <= module.GetBoundingBox().GetBottom()
            ), None)
            if blocker is None:
                if not obstructed_only:
                    add_trace(board, net, start, end)
                continue
            if obstructed_only:
                route = grid_router.find_route(
                    board,
                    net,
                    start,
                    end,
                    preferred_layer=0,
                    required_end_layer=0,
                )
                grid_router.apply_route(board, net, start, end, route)
            continue

        if obstructed_only:
            continue
        # Rank transitions run at the board edge. Clock remains on top; data
        # changes to the bottom so the two transitions cannot cross each other.
        right_side = start.x > origin
        direction = 1 if right_side else -1
        is_clock = nodes[0][1] == "6"
        distance_mm = (3.0 if right_side else 8.0) if is_clock else (1.0 if right_side else 6.0)
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


def route_control_signals(board, net_by_name, pads, only=None) -> None:
    """Route buses, controls, and level-shifted LED inputs as connected trees."""
    prefixes = (Net.SENSE_IRQ, "SPI_", Net.LED_CLOCK, Net.LED_DATA)
    selected = []
    for connection in sources.netlist()["connections"]:
        name = connection["name"]
        if name and name.startswith(prefixes) and (only is None or name in only):
            selected.append(connection)
    # Reserve the longest shared trunks before short button branches.
    def signal_priority(item):
        name = item["name"]
        order = {Net.SENSE_IRQ: 0, Net.I2C_SDA: 1, Net.I2C_SCL: 2}
        return (order.get(name, 3), name)

    selected.sort(key=signal_priority)
    for connection in selected:
        name = connection["name"]
        nodes = [tuple(node) for node in connection["pads"]]
        nodes.sort(key=lambda node: (node[0] != "J1", node[0], node[1]))
        remaining = set(range(1, len(nodes)))
        connected = {0}
        while remaining:
            left, right = min(
                ((a, b) for a in connected for b in remaining),
                key=lambda pair: abs(pads[nodes[pair[0]]].GetPosition().x - pads[nodes[pair[1]]].GetPosition().x)
                + abs(pads[nodes[pair[0]]].GetPosition().y - pads[nodes[pair[1]]].GetPosition().y),
            )
            start = pads[nodes[left]].GetPosition()
            end = pads[nodes[right]].GetPosition()
            net = net_by_name[name]
            preferred_layer = 1 if name in {Net.I2C_SDA, Net.I2C_SCL, Net.SPI_DATA} else 0
            start_pad, end_pad = pads[nodes[left]], pads[nodes[right]]
            if start_pad.IsOnLayer(pcbnew.F_Cu) and not start_pad.IsOnLayer(pcbnew.B_Cu):
                preferred_layer = 0
            required_end_layer = (
                0
                if end_pad.IsOnLayer(pcbnew.F_Cu) and not end_pad.IsOnLayer(pcbnew.B_Cu)
                else None
            )
            try:
                route = grid_router.find_route(
                    board,
                    net,
                    start,
                    end,
                    preferred_layer=preferred_layer,
                    required_end_layer=required_end_layer,
                    allow_vias=True,
                )
            except RuntimeError as error:
                raise RuntimeError(f"{error}: {nodes[left]} -> {nodes[right]}") from error
            grid_router.apply_route(board, net, start, end, route)
            connected.add(right)
            remaining.remove(right)


def route_internal_buses(board, net_by_name, pads) -> None:
    """Route shared low-speed buses on the isolated sixth-layer signal plane."""
    connections = {item["name"]: item for item in sources.netlist()["connections"]}
    layer_choices = {
        Net.I2C_SDA: (pcbnew.In4_Cu,),
        Net.I2C_SCL: (pcbnew.In5_Cu,),
        Net.SENSE_IRQ: (pcbnew.In6_Cu,),
    }
    for name in (Net.I2C_SDA, Net.I2C_SCL, Net.SENSE_IRQ):
        nodes = [tuple(node) for node in connections[name]["pads"]]
        nodes.sort(key=lambda node: (node[0] != "J1", node[0], node[1]))
        connected = {0}
        remaining = set(range(1, len(nodes)))
        net = net_by_name[name]
        while remaining:
            left, right = min(
                ((a, b) for a in connected for b in remaining),
                key=lambda pair: abs(
                    pads[nodes[pair[0]]].GetPosition().x
                    - pads[nodes[pair[1]]].GetPosition().x
                )
                + abs(
                    pads[nodes[pair[0]]].GetPosition().y
                    - pads[nodes[pair[1]]].GetPosition().y
                ),
            )
            start = pads[nodes[left]].GetPosition()
            end = pads[nodes[right]].GetPosition()
            route = grid_router.find_route(
                board,
                net,
                start,
                end,
                preferred_layer=0,
                allow_vias=len(layer_choices[name]) > 1,
                layers=layer_choices[name],
            )
            grid_router.apply_route(board, net, start, end, route)
            connected.add(right)
            remaining.remove(right)


def route_buttons(board, net_by_name, pads) -> None:
    """Connect both switch contacts and route each control to the Pi header."""
    names = (
        ButtonNet.F3,
        ButtonNet.F4,
        ButtonNet.F5,
        ButtonNet.RESET,
        ButtonNet.PASS,
        ButtonNet.F1,
        ButtonNet.F2,
        ButtonNet.OK,
        ButtonNet.RIGHT,
        ButtonNet.LEFT,
        ButtonNet.DOWN,
        ButtonNet.UP,
    )
    connections = {item["name"]: item for item in sources.netlist()["connections"]}
    for index, name in enumerate(names):
        nodes = [tuple(node) for node in connections[name]["pads"]]
        pi = next(node for node in nodes if node[0] == "J1")
        switch_node = next(node for node in nodes if node[0].startswith("SW"))
        module = next(
            footprint for footprint in board.GetFootprints()
            if footprint.GetReference() == switch_node[0]
        )
        primary = next(pad for pad in module.Pads() if pad.GetNumber() == "1")
        duplicate = next(pad for pad in module.Pads() if pad.GetNumber() == "1b")
        net = net_by_name[name]
        add_trace(
            board,
            net,
            primary.GetPosition(),
            duplicate.GetPosition(),
            pcbnew.B_Cu,
        )
        try:
            route = grid_router.find_route(
                board,
                net,
                pads[pi].GetPosition(),
                primary.GetPosition(),
                preferred_layer=1 - index % 2,
            )
        except RuntimeError:
            fallback_layers = {
                ButtonNet.F1: pcbnew.In4_Cu,
                ButtonNet.LEFT: pcbnew.In4_Cu,
                ButtonNet.OK: pcbnew.In5_Cu,
                ButtonNet.DOWN: pcbnew.In5_Cu,
                ButtonNet.F3: pcbnew.In6_Cu,
                ButtonNet.RIGHT: pcbnew.In6_Cu,
            }
            signal_layers = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)
            preferred = fallback_layers.get(
                name, signal_layers[index % len(signal_layers)]
            )
            candidates = (preferred,) + tuple(
                layer for layer in signal_layers if layer != preferred
            )
            start = pads[pi].GetPosition()
            direction = 1 if pcbnew.ToMM(start.y) > 340.0 else -1
            launch = pcbnew.VECTOR2I(
                start.x + pcbnew.FromMM(
                    0.8 if name == ButtonNet.F3 or index % 2 else -0.8
                ),
                start.y + direction * pcbnew.FromMM(4.5),
            )
            for layer in candidates:
                try:
                    route = grid_router.find_route(
                        board,
                        net,
                        launch,
                        primary.GetPosition(),
                        preferred_layer=0,
                        allow_vias=False,
                        layers=(layer,),
                        diagonals=True,
                    )
                    break
                except RuntimeError:
                    continue
            else:
                raise RuntimeError(f"no internal button route for {name}")
            add_trace(board, net, start, launch, layer)
            grid_router.apply_route(
                board, net, launch, primary.GetPosition(), route
            )
        else:
            grid_router.apply_route(
                board, net, pads[pi].GetPosition(), primary.GetPosition(), route
            )


def route_square_sensors(board, net_by_name, pads) -> None:
    """Route every reed input on a clearance-aware outer-layer grid."""
    for connection in sources.netlist()["connections"]:
        name = connection["name"]
        if not name or not name.startswith("SQ_"):
            continue
        nodes = [tuple(node) for node in connection["pads"]]
        if len(nodes) != 2:
            raise RuntimeError(f"{name}: square sensor net must have two pads")
        start, end = (pads[node].GetPosition() for node in nodes)
        net = net_by_name[name]
        route = grid_router.find_route(board, net, start, end)
        grid_router.apply_route(board, net, start, end, route)


def route_input_power(board, net_by_name, pads) -> None:
    """Route the short protected high-current input path at 1.5 mm width."""
    for name, left, right in (
        (Net.DC_INPUT, ("J3", "1"), ("F1", "1")),
        (Net.DC_FUSED, ("F1", "2"), ("SW13", "1")),
    ):
        add_trace(
            board,
            net_by_name[name],
            pads[left].GetPosition(),
            pads[right].GetPosition(),
            width=rules.POWER_TRACE_WIDTH_MM,
        )


def fanout_power(board, net_by_name) -> None:
    """Connect surface-mount power pads to dedicated internal planes."""
    for module in board.GetFootprints():
        centre = module.GetPosition()
        for pad in module.Pads():
            name = pad.GetNetname()
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or name not in {Net.GROUND, Net.FIVE_VOLTS}:
                continue
            at = pad.GetPosition()
            dx, dy = at.x - centre.x, at.y - centre.y
            length = max(1, round((dx * dx + dy * dy) ** 0.5))
            distance = pcbnew.FromMM(0.4)
            escaped = pcbnew.VECTOR2I(
                at.x + dx * distance // length,
                at.y + dy * distance // length,
            )
            if (
                pcbnew.FromMM(170) < at.x < pcbnew.FromMM(230)
                and pcbnew.FromMM(340) < at.y < pcbnew.FromMM(350)
            ):
                escaped = pcbnew.VECTOR2I(
                    at.x + (pcbnew.FromMM(4.0) if dx > 0 else -pcbnew.FromMM(4.0)),
                    at.y,
                )
            add_trace(board, net_by_name[name], at, escaped)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(escaped)
            via.SetWidth(pcbnew.FromMM(rules.VIA_PAD_MM))
            via.SetDrill(pcbnew.FromMM(rules.VIA_DRILL_MM))
            via.SetNet(net_by_name[name])
            board.Add(via)


def add_mounting_holes(board: pcbnew.BOARD) -> None:
    """Add one plated-copper-free screw clearance over every case boss."""
    shared = sources.dimensions()
    diameter = shared.PCB_MOUNTING_HOLE_DIAMETER_MM
    for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM, 1):
        module = pcbnew.FOOTPRINT(board)
        module.SetReference(f"H{index}")
        module.SetValue("M3 mounting hole")
        module.SetBoardOnly(True)
        module.Reference().SetVisible(False)
        module.Value().SetVisible(False)
        module.SetPosition(point(x, y))
        board.Add(module)
        pad = pcbnew.PAD(module)
        pad.SetNumber("")
        pad.SetPosition(point(x, y))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        size = pcbnew.FromMM(diameter)
        pad.SetSize(pcbnew.VECTOR2I(size, size))
        pad.SetDrillSize(pcbnew.VECTOR2I(size, size))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetLayerSet(pad.UnplatedHoleMask())
        module.Add(pad)
        radius = diameter / 2 + 0.5
        corners = ((x - radius, y - radius), (x + radius, y - radius), (x + radius, y + radius), (x - radius, y + radius))
        for corner_index, start in enumerate(corners):
            line = pcbnew.PCB_SHAPE(module)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(point(*start))
            line.SetEnd(point(*corners[(corner_index + 1) % 4]))
            line.SetLayer(pcbnew.F_CrtYd)
            line.SetWidth(pcbnew.FromMM(0.05))
            module.Add(line)


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
    for name, layer in (
        (Net.GROUND, pcbnew.In1_Cu),
        (Net.FIVE_VOLTS, pcbnew.In2_Cu),
        (Net.THREE_VOLTS_THREE, pcbnew.In3_Cu),
    ):
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
    board.SetCopperLayerCount(rules.COPPER_LAYERS)
    settings = board.GetDesignSettings()
    settings.m_MinClearance = pcbnew.FromMM(rules.CLEARANCE_MM)
    settings.m_TrackMinWidth = pcbnew.FromMM(rules.TRACE_WIDTH_MM)
    settings.m_HoleClearance = pcbnew.FromMM(0.25)
    settings.m_HoleToHoleMin = pcbnew.FromMM(0.25)
    settings.m_CopperEdgeClearance = pcbnew.FromMM(rules.POUR_TO_OUTLINE_MM)
    settings.m_ViasMinSize = pcbnew.FromMM(rules.VIA_PAD_MM)
    settings.m_ViasMinAnnularWidth = pcbnew.FromMM(
        rules.annular_ring(rules.VIA_PAD_MM, rules.VIA_DRILL_MM)
    )
    settings.m_MinThroughDrill = pcbnew.FromMM(rules.PCBWAY_MIN_DRILL_MM)
    settings.m_SilkClearance = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)
    settings.m_SolderMaskMinWidth = pcbnew.FromMM(rules.PCBWAY_MIN_MASK_DAM_MM)
    pad_nets, names = connectivity()
    net_by_name = {}
    for code, name in enumerate(sorted(set(names)), 1):
        net = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(net)
        net_by_name[name] = net
    pads = add_footprints(board, net_by_name, pad_nets)
    add_outline(board)
    add_mounting_holes(board)
    route_led_chain(board, net_by_name, pads)
    fanout_power(board, net_by_name)
    route_square_sensors(board, net_by_name, pads)
    route_led_chain(board, net_by_name, pads, obstructed_only=True)
    route_control_signals(
        board,
        net_by_name,
        pads,
        only={Net.SPI_CLOCK, Net.SPI_DATA, Net.LED_CLOCK, Net.LED_DATA},
    )
    route_buttons(board, net_by_name, pads)
    route_internal_buses(board, net_by_name, pads)
    route_input_power(board, net_by_name, pads)
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
