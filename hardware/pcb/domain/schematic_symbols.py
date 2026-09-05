"""KiCad symbol templates and stable identities, independent of board layout.

Library symbols describe physical pins; instances add approved product metadata.
Keep UUID input names stable: KiCad uses them to identify objects across writes.
"""

from __future__ import annotations

import uuid

from shared.components import ComponentSpec

NAMESPACE = uuid.UUID("83abf953-6539-4c7d-9e0f-e3b5ac2c4f3b")
ROOT_UUID = uuid.uuid5(NAMESPACE, "root")


def uid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def library_symbol_lines(
    reference: str, physical_pins: list[str], offsets: list[float]
) -> list[str]:
    """Draw a generic symbol with one pin per physical package pad."""
    lines: list[str] = []
    height = max(2.54, len(physical_pins) * 2.54)
    symbol = f"Generated:{reference}"
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
            f'      (property "Value" "{reference}" (at 1.27 2.54 0)',
            "        (effects (font (size 1.27 1.27)))",
            "      )",
            '      (property "Footprint" "" (at 0 0 0)',
            "        (effects (font (size 1.27 1.27)) (hide yes))",
            "      )",
            '      (property "Datasheet" "~" (at 0 0 0)',
            "        (effects (font (size 1.27 1.27)) (hide yes))",
            "      )",
            (
                '      (property "Description" "Generated physical-pin '
                f'symbol for {reference}" (at 0 0 0)'
            ),
            "        (effects (font (size 1.27 1.27)) (hide yes))",
            "      )",
            f'      (symbol "{reference}_0_1"',
            f"        (rectangle (start -1.27 {-height / 2:.3f}) (end 3.81 {height / 2:.3f})",
            "          (stroke (width 0.254) (type default))",
            "          (fill (type background))",
            "        )",
            "      )",
            f'      (symbol "{reference}_1_1"',
        ]
    )
    for physical, offset in zip(physical_pins, offsets, strict=True):
        lines.extend(
            [
                f"        (pin bidirectional line (at -5.08 {offset:.3f} 0) (length 3.81)",
                f'          (name "{physical}" (effects (font (size 1.27 1.27))))',
                f'          (number "{physical}" (effects (font (size 1.27 1.27))))',
                "        )",
            ]
        )
    lines.extend(["      )", "      (embedded_fonts no)", "    )"])
    return lines


def instance_lines(
    reference: str,
    spec: ComponentSpec,
    physical_pins: list[str],
    x: float,
    y: float,
) -> list[str]:
    """Place a library symbol and attach the reviewed part and pin identities."""
    lines: list[str] = []
    symbol_uuid = uid(f"symbol:{reference}")
    lines.extend(
        [
            "  (symbol",
            f'    (lib_id "Generated:{reference}")',
            f"    (at {x:.3f} {y:.3f} 0)",
            "    (unit 1)",
            "    (exclude_from_sim no)",
            "    (in_bom yes)",
            "    (on_board yes)",
            "    (dnp no)",
            f'    (uuid "{symbol_uuid}")',
            (
                f'    (property "Reference" "{reference}" (at '
                f"{x + 1.27:.3f} {y - 2.54:.3f} 0)"
            ),
            "      (effects (font (size 1.27 1.27)))",
            "    )",
            (
                f'    (property "Value" "{spec.mpn}" (at '
                f"{x + 1.27:.3f} {y + 2.54:.3f} 0)"
            ),
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
    for pad_index, physical in enumerate(physical_pins):
        lines.extend(
            [
                f'    (pin "{physical}"',
                f'      (uuid "{uid(f"pin:{reference}:{pad_index}")}")',
                "    )",
            ]
        )
    lines.extend(
        [
            "    (instances",
            '      (project "chess-board"',
            f'        (path "/{ROOT_UUID}" (reference "{reference}") (unit 1))',
            "      )",
            "    )",
            "  )",
        ]
    )
    return lines


def render_symbol_library(schematic: str) -> str:
    """Extract the embedded symbols without changing their serialized ordering."""
    lines = schematic.splitlines()
    start = lines.index("  (lib_symbols") + 1
    end = next(index for index in range(start, len(lines)) if lines[index] == "  )")
    symbols = [line.removeprefix("  ") for line in lines[start:end]]
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
