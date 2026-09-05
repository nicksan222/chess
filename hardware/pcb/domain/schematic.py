"""KiCad-independent schematic composition from a validated board design.

This module owns page layout and logical endpoint labels; schematic_symbols
owns physical-pin symbol templates. Only the CLI chooses an artifact path.
"""

from __future__ import annotations

from itertools import pairwise

from domain.design import BoardDesign
from domain.schematic_symbols import (
    ROOT_UUID,
    instance_lines,
    library_symbol_lines,
    uid,
)
from shared.components import COMPONENTS

SYMBOL_COLUMNS = 20
SYMBOL_COLUMN_PITCH_MM = 55.88
SYMBOL_ROW_GAP_MM = 10.16

EndpointKey = tuple[str, str]


def connectivity(
    design: BoardDesign,
) -> tuple[dict[EndpointKey, str], set[EndpointKey]]:
    """Index schematic endpoints through the shared validated connection graph."""
    graph = design.connections
    nets: dict[EndpointKey, str] = {}
    no_connects: set[EndpointKey] = set()
    for connection in graph.connections:
        if connection.no_connect:
            no_connects.update(connection.endpoints)
        else:
            nets.update(
                (endpoint, connection.name) for endpoint in connection.endpoints
            )
    return nets, no_connects


def row_centres(pin_counts: list[int]) -> list[float]:
    """Space symbol rows according to their tallest neighbouring members."""
    if not pin_counts:
        return []
    row_pin_counts = [
        max(pin_counts[start : start + SYMBOL_COLUMNS])
        for start in range(0, len(pin_counts), SYMBOL_COLUMNS)
    ]
    centres = [25.4]
    for previous, current in pairwise(row_pin_counts):
        centres.append(centres[-1] + (previous + current) * 1.27 + SYMBOL_ROW_GAP_MM)
    return centres


def render(design: BoardDesign) -> str:
    """Compose a deterministic sheet without reading or writing board artifacts."""
    nets, no_connects = connectivity(design)
    placed = design.placements
    lines = [
        "(kicad_sch",
        "  (version 20250114)",
        '  (generator "chess-board-generator")',
        '  (generator_version "1.0")',
        f'  (uuid "{ROOT_UUID}")',
        '  (paper "A0")',
        "  (title_block",
        f'    (title "{design.title}")',
        f'    (rev "{design.revision}")',
        '    (company "Chess")',
        '    (comment 1 "Generated from board/data/netlist.json; do not hand edit")',
        "  )",
        "  (lib_symbols",
    ]

    # Preserve pad order across templates, endpoint labels, and UUID pin indices.
    # Symbols show physical numbers; connectivity below uses logical pin names.
    layouts = {}
    for item in placed:
        pads = list(item.pads())
        offsets = [index * 2.54 - (len(pads) - 1) * 1.27 for index in range(len(pads))]
        layouts[item.reference] = (pads, offsets)
        lines.extend(
            library_symbol_lines(item.reference, [pad[1] for pad in pads], offsets)
        )
    lines.append("  )")

    row_y_positions = row_centres([len(layouts[item.reference][0]) for item in placed])

    for item_index, item in enumerate(placed):
        component = design.component(item.reference)
        spec = COMPONENTS[component.spec.part_key]
        pads, offsets = layouts[item.reference]
        column = item_index % SYMBOL_COLUMNS
        row = item_index // SYMBOL_COLUMNS
        # Row pitch follows the tallest symbols in adjacent rows. This keeps the
        # 40-pin Pi header clear without turning rows of two-pin passives into a
        # many-metre-tall schematic.
        x = 25.4 + column * SYMBOL_COLUMN_PITCH_MM
        y = row_y_positions[row]
        for pad_index, (pad, offset) in enumerate(zip(pads, offsets, strict=True)):
            logical, _physical, _position, _definition = pad
            endpoint_x, endpoint_y = x - 5.08, y - offset
            key = (item.reference, logical)
            if key in no_connects:
                lines.extend(
                    [
                        "  (no_connect",
                        f"    (at {endpoint_x:.3f} {endpoint_y:.3f})",
                        f'    (uuid "{uid(f"nc:{item.reference}:{pad_index}")}")',
                        "  )",
                    ]
                )
            else:
                name = nets[key]
                lines.extend(
                    [
                        f'  (global_label "{name}"',
                        "    (shape bidirectional)",
                        f"    (at {endpoint_x:.3f} {endpoint_y:.3f} 0)",
                        "    (effects (font (size 1.27 1.27)) (justify right))",
                        f'    (uuid "{uid(f"label:{item.reference}:{pad_index}")}")',
                        '    (property "Intersheetrefs" "${INTERSHEET_REFS}" (at 0 0 0)',
                        "      (effects (font (size 1.27 1.27)) (hide yes))",
                        "    )",
                        "  )",
                    ]
                )
        lines.extend(
            instance_lines(item.reference, spec, [pad[1] for pad in pads], x, y)
        )
    lines.extend(
        [
            "  (sheet_instances",
            '    (path "/" (page "1"))',
            "  )",
            "  (embedded_fonts no)",
            ")",
        ]
    )
    return "\n".join(lines) + "\n"
