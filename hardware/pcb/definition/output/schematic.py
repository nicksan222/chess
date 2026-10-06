"""Hierarchical KiCad schematic rendering from the native board.

Role: writes the human-readable schematic for review. It is *derived* from the
native board (footprints, their `Assembly` field and actual pad-to-net assignment);
nothing here is a source of connectivity. Output is an overview sheet plus one sheet
per subsystem (power, controls, and one per Hall bank which also holds that bank's
squares), a generated symbol library and a `sym-lib-table`. Nets are shown with
global labels on each pin rather than drawn wires, so a sheet is a pin-by-pin
net listing that KiCad can ERC and cross-check against the PCB.

Everything is deterministic (UUIDs come from `symbols.uid`) so regenerating an
unchanged design yields identical files. Never hand-edit the generated output.
"""

from __future__ import annotations

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
from pcb.definition.parts.catalog import PCB_PARTS
from shared import dimensions
from shared.components import COMPONENTS
from shared.electronics import Endpoint

# Layout of symbols on a sheet, in schematic mm (KiCad grid is 1.27 mm): up to
# four symbols per row.
SYMBOL_COLUMNS = 4

# Horizontal distance between symbol columns, wide enough for the net labels.
SYMBOL_COLUMN_PITCH_MM = 48.26

# Extra vertical space between rows, beyond the symbols' own heights.
SYMBOL_ROW_GAP_MM = 10.16


def connectivity(
    design: pcbnew.BOARD,
) -> tuple[dict[Endpoint[str], str], set[Endpoint[str]]]:
    """Index schematic endpoints through the shared validated connection graph.

    Returns (net name per endpoint, endpoints marked no-connect). Pads whose net
    starts with "unconnected-" are the deliberate no-connects from `no_connect()`.
    """
    nets: dict[Endpoint[str], str] = {}
    no_connects: set[Endpoint[str]] = set()
    for name, endpoints in connections(design).items():
        if name.startswith("unconnected-"):
            no_connects.update(endpoints)
        else:
            nets.update((endpoint, name) for endpoint in endpoints)
    return nets, no_connects


def row_centres(pin_counts: list[int]) -> list[float]:
    """Space symbol rows according to their tallest neighbouring members.

    Takes the pin count of each placed symbol (in slot order) and returns each
    row's centre y. A symbol is 2.54 mm per pin tall, so spacing by the tallest
    symbol per row keeps the 40-pin header clear without making rows of two-pin
    parts huge.
    """
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
    """Compose a deterministic sheet without reading or writing board artifacts.

    `members` are the footprints on this sheet in display order and `sheet` its
    name (used to derive UUIDs). Steps: header and title block; library symbols;
    slot assignment (one column/row per symbol, new assembly starts a new row);
    row headings; then each symbol with a global label or no-connect per pin.
    """
    # Connectivity is read from the board's pads, so labels cannot disagree with it.
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

    # Assign each footprint a (row, column) slot. A repeated square occupies one
    # complete row. A two-part bank header must
    # not push half the following square onto a different row.
    slots: dict[str, int] = {}
    slot = 0
    previous_assembly = ""
    counts: list[int] = []
    headings: dict[int, str] = {}
    for component in members:
        # Start a new row whenever the assembly changes, and record its heading.
        if component.GetFieldText("Assembly") != previous_assembly:
            slot = ((slot + SYMBOL_COLUMNS - 1) // SYMBOL_COLUMNS) * SYMBOL_COLUMNS
            headings[slot // SYMBOL_COLUMNS] = component.GetFieldText("Assembly")
        previous_assembly = component.GetFieldText("Assembly")
        slots[component.GetReference()] = slot
        counts.extend([0] * (slot + 1 - len(counts)))
        counts[slot] = len(layouts[component.GetReference()][0])
        slot += 1
    row_y_positions = row_centres(counts)
    # One bold heading above each assembly's row (e.g. "square/A1").
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
        # Each pin gets either a no-connect flag or a global label with its net name.
        # The label sits at the pin end (5.08 mm left of the symbol), so two pins on
        # the same net are connected by name, and labels line up with the pin rows.
        for pad_index, (pad, offset) in enumerate(zip(pads, offsets, strict=True)):
            logical = logical_pin(pad)
            endpoint_x, endpoint_y = x - 5.08, y - offset
            key = Endpoint(item.GetReference(), logical)
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
    # Single-page sheet bookkeeping required by KiCad's file format.
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
    component: pcbnew.FOOTPRINT, no_connects: set[Endpoint[str]] | None = None
) -> dict[str, tuple[str, str]]:
    """Physical pad numbers with semantic names and conservative electrical types.

    Supply/connector terminals remain passive: ERC does not model the external
    regulator, switch or fuse as an ideal voltage source. Active signal directions
    are checked, including open-drain Hall outputs and input-only expander ports.

    Returns {physical pad number: (symbol pin name, ERC pin type)}. Types are keyed
    on the part key and the typed pin name from `shared.electronics`; a pin not
    listed stays "passive". Choosing a wrong direction would hide real wiring
    mistakes (or raise false ERC errors), so change these only with the datasheet.
    """
    roles: dict[str, tuple[str, str]] = {}
    # Resolve the typed pin model so names come from datasheet roles, not pad numbers.
    model = PCB_PARTS[component.GetFieldText("PartKey")].new_model(
        component.GetReference()
    )
    for pad in component.Pads():
        logical, physical = logical_pin(pad), pad.GetNumber()
        endpoint = model.resolve_endpoint(logical)
        pin = endpoint.pin
        name = pin.name
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
        if Endpoint(component.GetReference(), logical) in (no_connects or set()):
            name = physical
        roles[physical] = (name, kind)
    return roles


def groups(design: pcbnew.BOARD) -> dict[str, tuple[pcbnew.FOOTPRINT, ...]]:
    """Partition parts into schematic sheets: power, controls (with the LED rail
    switch and the LED-chain terminators), one per Hall bank.

    A bank sheet holds the bank's expander/capacitor followed by its eight squares,
    in channel order, so the schematic mirrors the sensing hierarchy. Dict order is
    the sheet order in the overview.
    """

    def members(assembly: str) -> tuple[pcbnew.FOOTPRINT, ...]:
        return tuple(f for f in parts(design) if f.GetFieldText("Assembly") == assembly)

    # The LED chain's rank-turn terminators (S5) join the LED buffer's sheet.
    result = {
        "power": members("power"),
        "controls": members("controls") + members("led-switch") + members("led-chain"),
    }
    for bank in dimensions.HALL_BANKS:
        bank_members = list(members(f"sensing/{bank.label}"))
        for position in bank.members:
            bank_members.extend(members(f"square/{position.name}"))
        result[f"bank-{bank.label}"] = tuple(bank_members)
    return result


def render(design: pcbnew.BOARD | None = None) -> str:
    """Overview links to subsystem sheets; global nets cross sheet boundaries.

    The top sheet contains only sheet symbols (four per row, linking each
    `<name>.kicad_sch`); connectivity itself lives in the per-sheet global labels.
    """
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
    """Write the overview, all sheets, the combined symbol library and its table.

    `out` is the (staging) output directory chosen by the caller. The library is
    gathered from each rendered sheet so it contains exactly the symbols used.
    """
    (out / "chess-board.kicad_sch").write_text(render(design))
    libraries: list[str] = []
    for name, members in groups(design).items():
        text = render_sheet(design, members, name)
        (out / f"{name}.kicad_sch").write_text(text)
        # Drop the library header/footer lines; keep only the symbol definitions.
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
    # Tell KiCad to resolve the "Generated" library from this project directory.
    (out / "sym-lib-table").write_text(
        '(sym_lib_table (version 7) (lib (name "Generated")(type "KiCad")(uri "${KIPRJMOD}/generated-symbols.kicad_sym")(options "")(descr "")))\n'
    )
