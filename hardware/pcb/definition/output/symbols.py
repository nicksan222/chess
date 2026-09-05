"""Deterministic KiCad symbol and UUID generation."""

from __future__ import annotations

import uuid

from shared.components import ComponentSpec

NAMESPACE = uuid.UUID("83abf953-6539-4c7d-9e0f-e3b5ac2c4f3b")

ROOT_UUID = uuid.uuid5(NAMESPACE, "root")


def uid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def library_symbol_lines(
    reference: str,
    physical_pins: list[str],
    offsets: list[float],
    pin_roles: dict[str, tuple[str, str]] | None = None,
    part_key: str = "",
) -> list[str]:
    """Draw passives or a named functional block with physical package pins."""
    lines: list[str] = []
    height = max(2.54, len(physical_pins) * 2.54)
    symbol = f"Generated:{reference}"
    width = max(
        3.81,
        max((len(name) for name, _ in (pin_roles or {}).values()), default=0) * 1.0
        + 5.08,
    )
    passive = part_key.startswith(("CAP_", "RES_"))
    lines.extend(
        [
            f'    (symbol "{symbol}"',
            "      (pin_names (offset 1.016)" + (" (hide yes))" if passive else ")"),
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
            *body_lines(part_key, height, width),
            "      )",
            f'      (symbol "{reference}_1_1"',
        ]
    )
    for physical, offset in zip(physical_pins, offsets, strict=True):
        pin_name, pin_kind = (pin_roles or {}).get(physical, (physical, "passive"))
        lines.extend(
            [
                f"        (pin {pin_kind} line (at -5.08 {offset:.3f} 0) (length 3.81)",
                f'          (name "{pin_name}" (effects (font (size 1.27 1.27))))',
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
    sheet_path: str = f"/{ROOT_UUID}",
) -> list[str]:
    """Place a library symbol with its approved part and pin identities."""
    lines: list[str] = []
    symbol_uuid = uid(f"symbol:{reference}")
    half_height = max(2.54, len(physical_pins) * 2.54) / 2
    label_x = x + (1.27 if spec.key.startswith(("CAP_", "RES_")) else 10.16)
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
                f"{label_x:.3f} {y - half_height - 2.54:.3f} 0)"
            ),
            "      (effects (font (size 1.27 1.27)))",
            "    )",
            (
                f'    (property "Value" "{spec.mpn}" (at '
                f"{label_x:.3f} {y + half_height + 2.54:.3f} 0)"
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
            f'        (path "{sheet_path}" (reference "{reference}") (unit 1))',
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


def body_lines(part_key: str, height: float, width: float) -> list[str]:
    """Small conventional capacitor/resistor glyphs; other parts are named blocks."""
    if not part_key.startswith(("CAP_", "RES_")):
        return [
            f"        (rectangle (start -1.27 {-height / 2:.3f}) (end {width:.3f} {height / 2:.3f})",
            "          (stroke (width 0.254) (type default)) (fill (type background)))",
        ]
    lines: list[str] = []
    # Leads enter from the left so the uniform global-label layout stays compact.
    paths = [
        ((-1.27, -1.27), (1.27, -1.27), (1.27, -0.635)),
        ((-1.27, 1.27), (1.27, 1.27), (1.27, 0.635)),
    ]
    if part_key.startswith("CAP_"):
        paths += [((0.0, -0.635), (2.54, -0.635)), ((0.0, 0.635), (2.54, 0.635))]
        if part_key == "CAP_1000U":
            paths += [
                ((3.175, -1.27), (4.445, -1.27)),
                ((3.81, -1.905), (3.81, -0.635)),
            ]
    else:
        paths += [
            (
                (0.635, -0.635),
                (1.905, -0.635),
                (1.905, 0.635),
                (0.635, 0.635),
                (0.635, -0.635),
            )
        ]
    for path in paths:
        points = " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in path)
        lines.append(
            f"        (polyline (pts {points}) (stroke (width 0.254) (type default)) (fill (type none)))"
        )
    return lines
