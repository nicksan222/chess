"""Hierarchical KiCad schematic rendering from the native board."""

from __future__ import annotations

from enum import StrEnum
from itertools import pairwise
from pathlib import Path

import pcbnew

from pcb.definition import board as definition
from pcb.definition.native import connections, logical_pin, parts
from pcb.definition.output.symbols import (
    ROOT_UUID,
    instance_lines,
    library_symbol_lines,
    render_symbol_library,
    uid,
)
from pcb.definition.parts.catalog import MODELS
from shared import dimensions
from shared.components import COMPONENTS
from shared.hall_banks import square

SYMBOL_COLUMNS = 4

SYMBOL_COLUMN_PITCH_MM = 48.26

SYMBOL_ROW_GAP_MM = 10.16

EndpointKey = tuple[str, str]


def connectivity(
    design: pcbnew.BOARD,
) -> tuple[dict[EndpointKey, str], set[EndpointKey]]:
    """Index schematic endpoints through the shared validated connection graph."""
    nets: dict[EndpointKey, str] = {}
    no_connects: set[EndpointKey] = set()
    for name, endpoints in connections(design).items():
        if name.startswith("unconnected-"):
            no_connects.update(endpoints)
        else:
            nets.update((endpoint, name) for endpoint in endpoints)
    return nets, no_connects


def row_centres(pin_counts: list[int]) -> list[float]:
    """Space symbol rows according to their tallest neighbouring members."""
    if not pin_counts:
        return []
    row_pin_counts = [
        max(pin_counts[start : start + SYMBOL_COLUMNS])
        for start in range(0, len(pin_counts), SYMBOL_COLUMNS)
    ]
    centres = [25.4 + row_pin_counts[0] * 1.27]
    for previous, current in pairwise(row_pin_counts):
        centres.append(centres[-1] + (previous + current) * 1.27 + SYMBOL_ROW_GAP_MM)
    return centres


def render_sheet(
    design: pcbnew.BOARD, members: tuple[pcbnew.FOOTPRINT, ...], sheet: str
) -> str:
    """Compose a deterministic sheet without reading or writing board artifacts."""
    nets, no_connects = connectivity(design)
    placed = members
    lines = [
        "(kicad_sch",
        "  (version 20250114)",
        '  (generator "chess-board-generator")',
        '  (generator_version "1.0")',
        f'  (uuid "{uid("sheet-root:" + sheet)}")',
        '  (paper "A4" portrait)',
        "  (title_block",
        f'    (title "{design.GetTitleBlock().GetTitle()}")',
        f'    (rev "{design.GetTitleBlock().GetRevision()}")',
        '    (company "Chess")',
        '    (comment 1 "Generated from definition/board.py; do not hand edit")',
        "  )",
        "  (lib_symbols",
    ]

    # Preserve pad order across templates, endpoint labels, and UUID pin indices.
    # Symbols show physical numbers; connectivity below uses logical pin names.
    layouts: dict[str, tuple[list[pcbnew.PAD], list[float]]] = {}
    for item in placed:
        pads = list(item.Pads())
        offsets = [index * 2.54 - (len(pads) - 1) * 1.27 for index in range(len(pads))]
        layouts[item.GetReference()] = (pads, offsets)
        lines.extend(
            library_symbol_lines(
                item.GetReference(),
                [pad.GetNumber() for pad in pads],
                offsets,
                pin_roles(item, no_connects),
                item.GetFieldText("PartKey"),
            )
        )
    lines.append("  )")

    # A repeated square occupies one complete row. A two-part bank header must
    # not push half the following square onto a different row.
    slots: dict[str, int] = {}
    slot = 0
    previous_assembly = ""
    counts: list[int] = []
    headings: dict[int, str] = {}
    for component in members:
        if component.GetFieldText("Assembly") != previous_assembly:
            slot = ((slot + SYMBOL_COLUMNS - 1) // SYMBOL_COLUMNS) * SYMBOL_COLUMNS
            headings[slot // SYMBOL_COLUMNS] = component.GetFieldText("Assembly")
        previous_assembly = component.GetFieldText("Assembly")
        slots[component.GetReference()] = slot
        counts.extend([0] * (slot + 1 - len(counts)))
        counts[slot] = len(layouts[component.GetReference()][0])
        slot += 1
    row_y_positions = row_centres(counts)
    for row, heading in headings.items():
        height = max(counts[row * SYMBOL_COLUMNS : (row + 1) * SYMBOL_COLUMNS]) * 1.27
        lines.extend(
            [
                f'  (text "{heading}" (at 25.4 {row_y_positions[row] - height - 7.62:.3f} 0)',
                "    (effects (font (size 1.52 1.52) (bold yes)) (justify left))",
                f'    (uuid "{uid("heading:" + heading)}"))',
            ]
        )

    for item in placed:
        component = item
        spec = COMPONENTS[component.GetFieldText("PartKey")]
        pads, offsets = layouts[item.GetReference()]
        column = slots[item.GetReference()] % SYMBOL_COLUMNS
        row = slots[item.GetReference()] // SYMBOL_COLUMNS
        # Row pitch follows the tallest symbols in adjacent rows. This keeps the
        # 40-pin Pi header clear without turning rows of two-pin passives into a
        # many-metre-tall schematic.
        x = 25.4 + column * SYMBOL_COLUMN_PITCH_MM
        y = row_y_positions[row]
        for pad_index, (pad, offset) in enumerate(zip(pads, offsets, strict=True)):
            logical = logical_pin(pad)
            endpoint_x, endpoint_y = x - 5.08, y - offset
            key = (item.GetReference(), logical)
            if key in no_connects:
                lines.extend(
                    [
                        "  (no_connect",
                        f"    (at {endpoint_x:.3f} {endpoint_y:.3f})",
                        f'    (uuid "{uid(f"nc:{item.GetReference()}:{pad_index}")}")',
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
                        f'    (uuid "{uid(f"label:{item.GetReference()}:{pad_index}")}")',
                        '    (property "Intersheetrefs" "${INTERSHEET_REFS}" (at 0 0 0)',
                        "      (effects (font (size 1.27 1.27)) (hide yes))",
                        "    )",
                        "  )",
                    ]
                )
        lines.extend(
            instance_lines(
                item.GetReference(),
                spec,
                [pad.GetNumber() for pad in pads],
                x,
                y,
                f"/{ROOT_UUID}/{uid('sheet:' + sheet)}",
            )
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


def pin_roles(
    component: pcbnew.FOOTPRINT, no_connects: set[EndpointKey] | None = None
) -> dict[str, tuple[str, str]]:
    """Physical pad numbers with semantic names and conservative electrical types.

    Supply/connector terminals remain passive: ERC does not model the external
    regulator, switch or fuse as an ideal voltage source. Active signal directions
    are checked, including open-drain Hall outputs and input-only expander ports.
    """
    roles: dict[str, tuple[str, str]] = {}
    model = MODELS[component.GetFieldText("PartKey")](component.GetReference())
    for pad in component.Pads():
        logical, physical = logical_pin(pad), pad.GetNumber()
        endpoint = model.resolve_endpoint(logical)
        pin = endpoint.pin
        name = pin.name if isinstance(pin, StrEnum) else str(pin)
        key = component.GetFieldText("PartKey")
        kind = "passive"
        if key == "SK9822":
            if name.endswith("_IN"):
                kind = "input"
            if name.endswith("_OUT"):
                kind = "output"
        elif key == "HALL_SENSOR" and name == "ACTIVE_LOW_OUTPUT":
            kind = "open_collector"
        elif key == "AHCT125" and name.startswith("BUFFER_"):
            kind = "tri_state" if name.endswith("_OUTPUT") else "input"
        elif key == "TCA9554":
            if name.startswith("ADDRESS_") or name == "I2C_CLOCK":
                kind = "input"
            elif name == "INTERRUPT":
                kind = "open_collector"
            elif name.startswith("P") or name == "I2C_DATA":
                kind = "bidirectional"
        elif key == "PI_ZERO_HEADER":
            if name.startswith(("SPI_DATA_", "SPI_CLOCK_")):
                kind = "output"
            elif name.startswith("BUTTON_"):
                kind = "input"
            elif name in {"I2C_SDA", "I2C_SCL"}:
                kind = "bidirectional"
        # KiCad incorporates symbolic pin names into NC net names. Preserve
        # published unconnected-(REF-PadN) identities for deliberate NCs.
        if (component.GetReference(), logical) in (no_connects or set()):
            name = physical
        roles[physical] = (name, kind)
    return roles


def groups(design: pcbnew.BOARD) -> dict[str, tuple[pcbnew.FOOTPRINT, ...]]:
    def members(assembly: str) -> tuple[pcbnew.FOOTPRINT, ...]:
        return tuple(f for f in parts(design) if f.GetFieldText("Assembly") == assembly)

    result = {"power": members("power"), "controls": members("controls")}
    for bank in dimensions.HALL_BANKS:
        bank_members = list(members(f"sensing/{bank.label}"))
        for coordinates in bank.members:
            bank_members.extend(members(f"square/{square(*coordinates)}"))
        result[f"bank-{bank.label}"] = tuple(bank_members)
    return result


def render(design: pcbnew.BOARD | None = None) -> str:
    """Overview links to subsystem sheets; global nets cross sheet boundaries."""
    design = design or definition.load()
    lines = [
        "(kicad_sch",
        "  (version 20250114)",
        '  (generator "chess-board-generator")',
        f'  (uuid "{ROOT_UUID}")',
        '  (paper "A3")',
        f'  (title_block (title "{design.GetTitleBlock().GetTitle()}") (rev "{design.GetTitleBlock().GetRevision()}"))',
        "  (lib_symbols)",
    ]
    for index, name in enumerate(groups(design)):
        x, y = 25.4 + (index % 4) * 88.9, 38.1 + (index // 4) * 63.5
        lines.extend(
            [
                "  (sheet",
                f"    (at {x} {y}) (size 76.2 38.1)",
                "    (stroke (width 0.254) (type default)) (fill (color 0 0 0 0))",
                f'    (uuid "{uid("sheet:" + name)}")',
                f'    (property "Sheetname" "{name}" (at {x} {y - 1.27} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
                f'    (property "Sheetfile" "{name}.kicad_sch" (at {x} {y + 39.37} 0) (effects (font (size 1.27 1.27)) (justify left top)))',
                f'    (instances (project "chess-board" (path "/{ROOT_UUID}" (page "{index + 2}"))))',
                "  )",
            ]
        )
    lines.extend(
        ['  (sheet_instances (path "/" (page "1")))', "  (embedded_fonts no)", ")", ""]
    )
    return "\n".join(lines)


def write(design: pcbnew.BOARD, out: Path) -> None:
    (out / "chess-board.kicad_sch").write_text(render(design))
    libraries: list[str] = []
    for name, members in groups(design).items():
        text = render_sheet(design, members, name)
        (out / f"{name}.kicad_sch").write_text(text)
        libraries.extend(render_symbol_library(text).splitlines()[4:-1])
    library = "\n".join(
        [
            "(kicad_symbol_lib",
            "  (version 20231120)",
            '  (generator "chess-board-generator")',
            '  (generator_version "1.0")',
            *libraries,
            ")",
            "",
        ]
    )
    (out / "generated-symbols.kicad_sym").write_text(library)
    (out / "sym-lib-table").write_text(
        '(sym_lib_table (version 7) (lib (name "Generated")(type "KiCad")(uri "${KIPRJMOD}/generated-symbols.kicad_sym")(options "")(descr "")))\n'
    )
