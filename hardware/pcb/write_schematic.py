#!/usr/bin/env python3
"""Compose the native KiCad schematic from reviewed connectivity and products."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARDWARE = ROOT.parent
sys.path[:0] = [str(ROOT), str(HARDWARE)]

from core import placement, sources  # noqa: E402
from shared.components import COMPONENTS  # noqa: E402

DESTINATION = ROOT / "chess-board.kicad_sch"
SYMBOL_LIBRARY = ROOT / "generated-symbols.kicad_sym"
SYMBOL_TABLE = ROOT / "sym-lib-table"
NAMESPACE = uuid.UUID("83abf953-6539-4c7d-9e0f-e3b5ac2c4f3b")
ROOT_UUID = uuid.uuid5(NAMESPACE, "root")


def uid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def effects(*, hidden: bool = False) -> list[str]:
    result = ["(effects", "  (font (size 1.27 1.27))"]
    if hidden:
        result.append("  (hide yes)")
    result.append(")")
    return result


def connectivity():
    nets = {}
    no_connects = set()
    for index, connection in enumerate(sources.netlist()["connections"], 1):
        name = connection["name"] or f"N${index}"
        for reference, logical_pin in connection["pads"]:
            key = (reference, logical_pin)
            if connection.get("no_connect"):
                no_connects.add(key)
            else:
                nets[key] = name
    return nets, no_connects


def render() -> str:
    nets, no_connects = connectivity()
    components = sources.netlist()["components"]
    placed = placement.build()
    lines = [
        "(kicad_sch",
        "  (version 20250114)",
        '  (generator "chess-board-generator")',
        '  (generator_version "1.0")',
        f'  (uuid "{ROOT_UUID}")',
        '  (paper "A0")',
        "  (title_block",
        '    (title "Code-composed chess board")',
        '    (rev "B-PROTOTYPE")',
        '    (company "Chess")',
        '    (comment 1 "Generated from design/netlist.json; do not hand edit")',
        "  )",
        "  (lib_symbols",
    ]

    layouts = {}
    for item in placed:
        pads = list(item.pads())
        offsets = [index * 2.54 - (len(pads) - 1) * 1.27 for index in range(len(pads))]
        layouts[item.reference] = (pads, offsets)
        height = max(2.54, len(pads) * 2.54)
        symbol = f"Generated:{item.reference}"
        lines.extend(
            [
                f'    (symbol "{symbol}"',
                "      (pin_names (offset 1.016))",
                "      (exclude_from_sim no)",
                "      (in_bom yes)",
                "      (on_board yes)",
                '      (property "Reference" "U" (at 1.27 -2.54 0)',
                "        (effects (font (size 1.27 1.27)))",
                "      )",
                f'      (property "Value" "{item.reference}" (at 1.27 2.54 0)',
                "        (effects (font (size 1.27 1.27)))",
                "      )",
                '      (property "Footprint" "" (at 0 0 0)',
                "        (effects (font (size 1.27 1.27)) (hide yes))",
                "      )",
                '      (property "Datasheet" "~" (at 0 0 0)',
                "        (effects (font (size 1.27 1.27)) (hide yes))",
                "      )",
                f'      (property "Description" "Generated physical-pin symbol for {item.reference}" (at 0 0 0)',
                "        (effects (font (size 1.27 1.27)) (hide yes))",
                "      )",
                f'      (symbol "{item.reference}_0_1"',
                f"        (rectangle (start -1.27 {-height / 2:.3f}) (end 3.81 {height / 2:.3f})",
                "          (stroke (width 0.254) (type default))",
                "          (fill (type background))",
                "        )",
                "      )",
                f'      (symbol "{item.reference}_1_1"',
            ]
        )
        for pad, offset in zip(pads, offsets, strict=True):
            _logical, physical, _position, _definition = pad
            lines.extend(
                [
                    f"        (pin bidirectional line (at -5.08 {offset:.3f} 0) (length 3.81)",
                    f'          (name "{physical}" (effects (font (size 1.27 1.27))))',
                    f'          (number "{physical}" (effects (font (size 1.27 1.27))))',
                    "        )",
                ]
            )
        lines.extend(["      )", "      (embedded_fonts no)", "    )"])
    lines.append("  )")

    columns = 16
    for item_index, item in enumerate(placed):
        entry = components[item.reference]
        spec = COMPONENTS[entry["part_key"]]
        pads, offsets = layouts[item.reference]
        column, row = item_index % columns, item_index // columns
        x, y = 25.4 + column * 71.12, 25.4 + row * 53.34
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
        symbol_uuid = uid(f"symbol:{item.reference}")
        lines.extend(
            [
                "  (symbol",
                f'    (lib_id "Generated:{item.reference}")',
                f"    (at {x:.3f} {y:.3f} 0)",
                "    (unit 1)",
                "    (exclude_from_sim no)",
                "    (in_bom yes)",
                "    (on_board yes)",
                "    (dnp no)",
                f'    (uuid "{symbol_uuid}")',
                f'    (property "Reference" "{item.reference}" (at {x + 1.27:.3f} {y - 2.54:.3f} 0)',
                "      (effects (font (size 1.27 1.27)))",
                "    )",
                f'    (property "Value" "{spec.mpn}" (at {x + 1.27:.3f} {y + 2.54:.3f} 0)',
                "      (effects (font (size 1.27 1.27)))",
                "    )",
                f'    (property "Footprint" "" (at {x:.3f} {y:.3f} 0)',
                "      (effects (font (size 1.27 1.27)) (hide yes))",
                "    )",
                f'    (property "Datasheet" "{spec.datasheet}" (at {x:.3f} {y:.3f} 0)',
                "      (effects (font (size 1.27 1.27)) (hide yes))",
                "    )",
                f'    (property "Description" "{spec.description}" (at {x:.3f} {y:.3f} 0)',
                "      (effects (font (size 1.27 1.27)) (hide yes))",
                "    )",
            ]
        )
        for pad_index, pad in enumerate(pads):
            _logical, physical, _position, _definition = pad
            lines.extend(
                [
                    f'    (pin "{physical}"',
                    f'      (uuid "{uid(f"pin:{item.reference}:{pad_index}")}")',
                    "    )",
                ]
            )
        lines.extend(
            [
                "    (instances",
                '      (project "chess-board"',
                f'        (path "/{ROOT_UUID}" (reference "{item.reference}") (unit 1))',
                "      )",
                "    )",
                "  )",
            ]
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


def render_symbol_library(schematic: str) -> str:
    lines = schematic.splitlines()
    start = lines.index("  (lib_symbols") + 1
    end = next(index for index in range(start, len(lines)) if lines[index] == "  )")
    symbols = [line[2:] if line.startswith("  ") else line for line in lines[start:end]]
    return "\n".join(
        [
            "(kicad_symbol_lib",
            "  (version 20231120)",
            '  (generator "chess-board-generator")',
            '  (generator_version "1.0")',
            *symbols,
            ")",
            "",
        ]
    )


def write() -> None:
    schematic = render()
    DESTINATION.write_text(schematic)
    SYMBOL_LIBRARY.write_text(render_symbol_library(schematic))
    SYMBOL_TABLE.write_text(
        '(sym_lib_table\n'
        '  (version 7)\n'
        '  (lib (name "Generated")(type "KiCad")'
        '(uri "${KIPRJMOD}/generated-symbols.kicad_sym")(options "")(descr ""))\n'
        ')\n'
    )
    print(f"wrote {DESTINATION}")
    print(f"wrote {SYMBOL_LIBRARY}")


if __name__ == "__main__":
    write()
