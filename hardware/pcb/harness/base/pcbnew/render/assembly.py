"""Assembly handoff derived from real packages and native KiCad placement."""

import csv
import math
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import cast

from shared.components import COMPONENTS
from shared.electronics.harness import HARNESS_PARTS, HARNESSES, render_harness_table

from ...circuit import Circuit
from ...component import BoardComponent
from ...net import Net
from ..pad import PadKind


def write_assembly[BoardNet: Net](circuit: Circuit[BoardNet], directory: Path) -> None:
    parts = {
        part.reference: cast(BoardComponent[StrEnum], part)
        for part in circuit.components()
    }
    path = directory / "positions.csv"
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        positions = list(reader)
    if (
        fields is None
        or {row["Ref"] for row in positions} != set(parts)
        or len(positions) != len(parts)
    ):
        raise ValueError("Native placement coverage must exactly match the board")
    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    smd: list[tuple[object, ...]] = []
    manual: list[tuple[object, ...]] = []
    for row in positions:
        part = parts[row["Ref"]]
        product = part.definition.product
        pattern = part.definition.land_pattern
        if pattern is None:
            raise ValueError(f"{part.reference}: missing land pattern")
        kinds = {pad.kind for pad in pattern.pads}
        mount = (
            "SMD"
            if kinds == {PadKind.SURFACE}
            else "Through-hole"
            if kinds == {PadKind.THROUGH_HOLE}
            else "Hybrid"
        )
        row["Package"] = product.package
        row["Val"] = product.part_number
        if row["Side"] not in ("top", "bottom") or not all(
            math.isfinite(float(row[key])) for key in ("PosX", "PosY", "Rot")
        ):
            raise ValueError(f"{part.reference}: invalid native placement")
        target = smd if mount == "SMD" else manual
        target.append(
            (
                part.reference,
                row["PosX"],
                row["PosY"],
                row["Rot"],
                row["Side"],
                product.package,
                product.part_number,
            )
        )
        grouped.setdefault(
            (product.manufacturer, product.part_number, product.package, mount), []
        ).append(part.reference)
    _write(
        path,
        tuple(fields),
        [tuple(row[field] for field in fields) for row in positions],
    )
    columns = (
        "Designator",
        "Mid X (mm)",
        "Mid Y (mm)",
        "Rotation",
        "Layer",
        "Package",
        "Manufacturer Part Number",
    )
    _write(directory / "assembly-smd.csv", columns, smd)
    _write(directory / "assembly-through-hole.csv", columns, manual)
    _write(
        directory / "assembly-bom.csv",
        (
            "Quantity",
            "Designators",
            "Manufacturer",
            "Manufacturer Part Number",
            "Package",
            "Type",
        ),
        [
            (len(refs), ", ".join(sorted(refs)), *key)
            for key, refs in sorted(grouped.items())
        ],
    )
    (directory / "harness.md").write_text(render_harness_table())
    quantities: Counter[str] = Counter()
    for items in HARNESS_PARTS.values():
        quantities.update(items)
    quantities.update({wire.far_part for wires in HARNESSES.values() for wire in wires})
    _write(
        directory / "harness-bom.csv",
        (
            "Product",
            "Quantity",
            "Manufacturer",
            "Manufacturer Part Number",
            "Package",
            "Purchase Unit",
            "Kit Usage",
        ),
        [
            (
                key,
                quantity,
                COMPONENTS[key].manufacturer,
                COMPONENTS[key].mpn,
                COMPONENTS[key].package,
                COMPONENTS[key].purchase_unit,
                COMPONENTS[key].kit_quantity(quantity),
            )
            for key, quantity in sorted(quantities.items())
        ],
    )
    (directory / "assembly.md").write_text(
        "# Assembly review files\n\n"
        "`assembly-bom.csv`: grouped on-board parts, quantities and mounting types.\n"
        "`assembly-smd.csv`: surface-mount placements; `assembly-through-hole.csv`: through-hole/hybrid placements for separate assembly review.\n"
        "Native KiCad millimetre XY, rotation and top/bottom conventions are retained; confirm origin, bottom-side orientation and pin 1 with the assembler.\n"
        "`positions.csv` includes all mounted parts with package/MPN identity.\n"
        "`harness.md` and `harness-bom.csv`: off-board wire assemblies, separate from the PCB BOM.\n\n"
        "These are local review exports. Stackup, electrical roles and physical manufacturing approval remain pending.\n"
    )


def _write(
    path: Path, columns: tuple[str, ...], rows: list[tuple[object, ...]]
) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)
