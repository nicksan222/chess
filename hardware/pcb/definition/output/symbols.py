"""Deterministic KiCad symbol and UUID generation.

Role: low-level text emitters for the generated schematic (`schematic.py`) and the
UUID scheme shared with the PCB (`native.py`). Symbols are written as KiCad
s-expression lines. Every symbol is a one-off "physical pin" symbol: its pins are
the footprint's pad numbers in pad order (named by datasheet role where known), so
the schematic can be cross-checked pad for pad against the board.

UUIDs are `uuid5` of a semantic name inside one fixed namespace, never random, so
regenerating an unchanged design reproduces identical identifiers and the PCB
footprint paths stay linked to their schematic symbols.
"""

from __future__ import annotations

import uuid

from shared.components import ComponentSpec

# Fixed namespace for all uuid5 identities. Changing it re-keys every UUID in the
# schematic and board (and breaks the PCB<->schematic links until both regenerate).
NAMESPACE = uuid.UUID("83abf953-6539-4c7d-9e0f-e3b5ac2c4f3b")

# Identity of the top-level (overview) sheet; the root of every footprint path.
ROOT_UUID = uuid.uuid5(NAMESPACE, "root")


def uid(name: str) -> str:
    """Stable UUID string for a semantic name such as "symbol:U1" or "sheet:power"."""
    return str(uuid.uuid5(NAMESPACE, name))


def library_symbol_lines(
    reference: str,
    physical_pins: list[str],
    offsets: list[float],
    pin_roles: dict[str, tuple[str, str]] | None = None,
    part_key: str = "",
) -> list[str]:
    """Draw passives or a named functional block with physical package pins.

    Returns the `lib_symbols` entry for one placed component. `physical_pins` are
    pad numbers and `offsets` their vertical positions (same order). `pin_roles`
    maps pad number to (displayed name, ERC pin type) from `schematic.pin_roles`;
    a pin without a role falls back to its number as a passive. Passives (CAP_/RES_)
    hide pin names for a conventional look. Box width grows with the longest pin name.
    """
    lines: list[str] = []
    # 2.54 mm (two KiCad grid steps) per pin, matching the pin offsets chosen by
    # the caller.
    height = max(2.54, len(physical_pins) * 2.54)
    # Symbols are per reference (not per part type): each is its own library entry.
    symbol = f"Generated:{reference}"
    # Wide enough for the longest pin name plus the box margin.
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
    # All pins sit on the left edge so the global labels can share one column.
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
    """Place a library symbol with its approved part and pin identities.

    Emits the schematic instance at (x, y): reference, value (the MPN), datasheet
    and description taken from the approved `ComponentSpec`, plus a UUID per pin.
    `sheet_path` is the hierarchical path that must match the footprint's path set
    in `native.place()`, which is what links symbol and footprint for parity checks.
    """
    lines: list[str] = []
    # Same name `native.place()` uses for the footprint path's final element.
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
    """Extract the embedded symbols without changing their serialized ordering.

    Reuses the `lib_symbols` block of a rendered sheet as a standalone library, so
    the library always matches the symbols the sheets actually reference.
    """
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
    """Small conventional capacitor/resistor glyphs; other parts are named blocks.

    Active parts are a plain rectangle sized by `height`/`width`. The 1000 uF
    capacitor (`CAP_560U`) gets an extra plus mark to show it is polarized.
    """
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
        if part_key == "CAP_560U":
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
