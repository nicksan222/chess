"""Check KiCad's exported netlist against the circuit's physical terminal map.

KiCad names intentionally unused pins in its schematic netlist. Copy those names
onto PCB pads only after checking the complete export; never repair connected
pins to hide a mismatch. The native schematic/PCB parity check follows this step.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import cast

import pcbnew

from pcb.harness import BoardComponent, Circuit, Net, NetConnection
from pcb.harness.base.pcbnew.render.identity import normalize_board_uuids
from pcb.harness.base.pcbnew.render.schematic import symbol_pins


def declared_connections[BoardNet: Net](
    circuit: Circuit[BoardNet],
) -> tuple[dict[str, set[tuple[str, str]]], set[tuple[str, str]]]:
    """Expand logical pin maps to every physical terminal in the land patterns."""
    expected: dict[str, set[tuple[str, str]]] = defaultdict(set)
    unused: set[tuple[str, str]] = set()
    for component in circuit.components():
        if not isinstance(component, BoardComponent):
            raise ValueError("PCB netlist needs BoardComponent instances")
        part = cast(BoardComponent[StrEnum], component)
        for number, pin in symbol_pins(part):
            connection = part.pins[pin]
            endpoint = (component.reference, number)
            if isinstance(connection, NetConnection):
                expected[connection.net.label].add(endpoint)
            else:
                unused.add(endpoint)
    return dict(expected), unused


def apply_netlist[BoardNet: Net](
    circuit: Circuit[BoardNet], exported_path: Path, board_path: Path, json_path: Path
) -> None:
    """Reject mismatched exports, then annotate unused PCB pads and write JSON."""
    expected, unused = declared_connections(circuit)
    exported: dict[str, set[tuple[str, str]]] = {}
    exported_unused: set[tuple[str, str]] = set()
    unused_names: dict[tuple[str, str], str] = {}
    for net in ET.parse(exported_path).findall("./nets/net"):
        name = net.attrib["name"]
        nodes = {
            (node.attrib["ref"], node.attrib["pin"]) for node in net.findall("node")
        }
        if name in expected:
            if name in exported:
                raise ValueError(f"duplicate schematic net: {name}")
            exported[name] = nodes
        elif name.startswith("unconnected-"):
            if len(nodes) != 1 or not nodes <= unused or nodes & exported_unused:
                raise ValueError(f"unexpected schematic no-connect: {name}")
            exported_unused.update(nodes)
            unused_names[next(iter(nodes))] = name
        else:
            raise ValueError(f"unexpected schematic net: {name}")
    if exported != expected or exported_unused != unused:
        raise ValueError("schematic netlist differs from declared component pin maps")
    board = pcbnew.LoadBoard(str(board_path))
    for (reference, pin), name in unused_names.items():
        footprint = board.FindFootprintByReference(reference)
        if footprint is None:
            raise ValueError(f"missing no-connect footprint: {reference}")
        pads = [pad for pad in footprint.Pads() if pad.GetNumber() == pin]
        if not pads:
            raise ValueError(f"missing no-connect pad: {reference}.{pin}")
        network = pcbnew.NETINFO_ITEM(board, name, board.GetNetCount())
        board.Add(network)
        for pad in pads:
            pad.SetNet(network)
    if not pcbnew.SaveBoard(str(board_path), board):
        raise OSError("KiCad could not save unused-pin net assignments")
    normalize_board_uuids(board, board_path)
    board_path.with_suffix(".kicad_prl").unlink(missing_ok=True)
    json_path.write_text(
        json.dumps(
            {name: sorted(nodes) for name, nodes in sorted(expected.items())}, indent=2
        )
        + "\n"
    )
