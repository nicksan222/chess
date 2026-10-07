"""Self-contained connection schematics derived solely from component pin maps.

Symbols expose named package terminals. Electrical pin roles are unspecified:
component definitions do not yet declare input/output/power roles, so ERC findings
are retained rather than inventing electrical semantics to make checks pass.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from ...circuit import Circuit
from ...component import BoardComponent
from ...connections import NetConnection
from ...net import Net

_NAMESPACE = uuid.UUID("c218aac3-13ed-48fc-89cb-bac8ba5d909a")
_EFFECTS = "(effects (font (size 1.27 1.27)))"


def identifier(key: str) -> str:
    """Stable identities link native footprints to schematic symbol instances."""
    return str(uuid.uuid5(_NAMESPACE, key))


def quoted(value: str) -> str:
    """Quote arbitrary product names and descriptions as KiCad strings."""
    return json.dumps(value, ensure_ascii=False)


@dataclass(frozen=True)
class SchematicFiles:
    root: Path
    sheets: tuple[Path, ...]
    symbol_paths: dict[str, str]


def _property(
    name: str, value: str, x: float, y: float, *, hidden: bool = False
) -> str:
    effects = (
        "(effects (font (size 1.27 1.27))" + (" (hide yes)" if hidden else "") + ")"
    )
    return f"(property {quoted(name)} {quoted(value)} (at {x:g} {y:g} 0) {effects})"


def _header(name: str, title: str, paper: str) -> str:
    return (
        f'(kicad_sch (version 20250114) (generator "chess_harness") '
        f'(uuid "{identifier(name)}") {paper} '
        f"(title_block (title {quoted(title)}))"
    )


def symbol_pins(component: BoardComponent[StrEnum]) -> tuple[tuple[str, StrEnum], ...]:
    """Expose every physical pad, including several pads of one logical pin."""
    pattern = component.definition.land_pattern
    if pattern is None:
        return tuple((str(pin), pin) for pin in component.definition.pin_type)
    return tuple((pad.number or str(pad.pin), pad.pin) for pad in pattern.pads)


def _symbol(component: BoardComponent[StrEnum]) -> str:
    product = component.definition.product
    height = (len(symbol_pins(component)) + 1) * 2.54
    key = product.key
    pins = "\n".join(
        f"(pin unspecified line (at -22.86 {-index * 2.54:g} 0) (length 5.08) "
        f"(name {quoted(pin.name)} {_EFFECTS}) (number {quoted(number)} {_EFFECTS}))"
        for index, (number, pin) in enumerate(symbol_pins(component), 1)
    )
    return (
        f'(symbol "Board:{key}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
        f"{_property('Reference', 'U', 0, 2.54)} {_property('Value', product.part_number, 0, 0)} "
        f'(symbol "{key}_0_1" (rectangle (start -17.78 0) (end 22.86 {-height:g}) '
        "(stroke (width 0.254) (type default)) (fill (type background)))) "
        f'(symbol "{key}_1_1" {pins}))'
    )


def write_schematic[BoardNet: Net](
    circuit: Circuit[BoardNet], directory: Path, name: str
) -> SchematicFiles:
    """Write paginated schematics, including embedded symbols and global nets.

    Twelve components per sheet reserve enough space for the largest pin count.
    No installed symbol libraries or a second wiring definition are required.
    The caller owns output staging and publication.
    """
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
        raise ValueError("project name must be a simple letter-led identifier")
    circuit.validate()
    components: list[BoardComponent[StrEnum]] = []
    for component in circuit.components():
        if not isinstance(component, BoardComponent):
            raise ValueError("schematic needs BoardComponent instances")
        components.append(cast(BoardComponent[StrEnum], component))
    libraries = {
        component.definition.product.key: component for component in components
    }
    (directory / "board.kicad_sym").write_text(
        '(kicad_symbol_lib (version 20241209) (generator "chess_harness")\n'
        + "\n".join(
            _symbol(part).replace('(symbol "Board:', '(symbol "', 1)
            for part in libraries.values()
        )
        + "\n)\n"
    )
    (directory / "sym-lib-table").write_text(
        '(sym_lib_table (version 7) (lib (name "Board") (type "KiCad") '
        '(uri "${KIPRJMOD}/board.kicad_sym") (options "") (descr "Generated component pin maps")))\n'
    )
    root_key = f"{name}/root"
    root_id = identifier(root_key)
    root = [_header(root_key, "Connection index", '(paper "A3")'), "(lib_symbols)"]
    paths: dict[str, str] = {}
    sheets: list[Path] = []
    for page, offset in enumerate(range(0, len(components), 12), 1):
        sheet_name = f"components-{page:02}"
        sheet_id = identifier(f"{name}/{sheet_name}")
        group = components[offset : offset + 12]
        libraries = {component.definition.product.key: component for component in group}
        row_heights = [
            max(len(symbol_pins(part)) for part in group[start : start + 3]) * 2.54
            + 25.4
            for start in range(0, len(group), 3)
        ]
        row_y = [25.4 + sum(row_heights[:index]) for index in range(len(row_heights))]
        height = max(210, row_y[-1] + row_heights[-1] + 50.8)
        content = [
            _header(
                f"{name}/{sheet_name}",
                f"Components {page}: {group[0].reference} to {group[-1].reference}",
                f'(paper "User" 420 {height:g})',
            ),
            "(lib_symbols "
            + "\n".join(_symbol(part) for part in libraries.values())
            + ")",
        ]
        for index, component in enumerate(group):
            x, y = 76.2 + (index % 3) * 127, row_y[index // 3]
            product = component.definition.product
            symbol_id = identifier(f"{name}/component/{component.reference}")
            paths[component.reference] = f"/{root_id}/{sheet_id}/{symbol_id}"
            properties = " ".join(
                _property(field, value, x, y - 5.08 + number * 2.54, hidden=number > 1)
                for number, (field, value) in enumerate(
                    (
                        ("Reference", component.reference),
                        ("Value", product.part_number),
                        ("Footprint", product.key),
                        ("Datasheet", product.datasheet),
                        ("Description", component.purpose),
                    )
                )
            )
            content.append(
                f'(symbol (lib_id "Board:{product.key}") (at {x:g} {y:g} 0) (unit 1) '
                f'(in_bom yes) (on_board yes) (dnp no) (uuid "{symbol_id}") {properties} '
                f'(instances (project "{name}" (path "/{root_id}/{sheet_id}" '
                f"(reference {quoted(component.reference)}) (unit 1)))))"
            )
            for number, (physical_pin, pin) in enumerate(symbol_pins(component), 1):
                connection = component.pins[pin]
                px, py = x - 22.86, y + number * 2.54
                key = f"{name}/{component.reference}/{physical_pin}"
                if isinstance(connection, NetConnection):
                    content.append(
                        f"(global_label {quoted(connection.net.label)} (shape passive) "
                        f"(at {px:g} {py:g} 0) (effects (font (size 1.016 1.016)) (justify right)) "
                        f'(uuid "{identifier(key + "/net")}"))'
                    )
                else:
                    content.append(
                        f'(no_connect (at {px:g} {py:g}) (uuid "{identifier(key + "/nc")}"))'
                    )
        path = directory / f"{sheet_name}.kicad_sch"
        path.write_text("\n".join(content) + "\n)\n")
        sheets.append(path)
        x, y = 20 + ((page - 1) % 4) * 95, 25 + ((page - 1) // 4) * 32
        root.append(
            f"(sheet (at {x} {y}) (size 75 18) (stroke (width 0.254) (type default)) "
            f'(fill (color 0 0 0 0)) (uuid "{sheet_id}") '
            f"{_property('Sheetname', sheet_name, x, y - 2)} "
            f"{_property('Sheetfile', path.name, x, y + 20)} "
            f'(instances (project "{name}" (path "/{root_id}" (page "{page + 1}")))))'
        )
    root.append('(sheet_instances (path "/" (page "1")))')
    root_path = directory / f"{name}.kicad_sch"
    root_path.write_text("\n".join(root) + "\n)\n")
    return SchematicFiles(root_path, tuple(sheets), paths)
