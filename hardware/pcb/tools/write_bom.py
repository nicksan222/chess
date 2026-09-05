#!/usr/bin/env python3
"""Write the purchasing BOM from approved product identities."""

from __future__ import annotations

import csv
import io
import sys
from collections import defaultdict
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
sys.path[:0] = [str(PCB_ROOT), str(HARDWARE_ROOT)]

from board import artifacts
from board import definition as board_definition
from domain.design import BoardDesign
from shared.components import COMPONENTS

EXTRA_ASSEMBLY_PARTS = (
    "PI_ZERO_2_W",
    "OLED_MODULE",
    "POWER_SUPPLY",
    "MICRO_SD",
)


def reference_sort_key(reference: str) -> tuple[str, int]:
    """Sort references naturally, including multi-letter prefixes such as HS."""
    prefix = reference.rstrip("0123456789")
    suffix = reference[len(prefix) :]
    return prefix, int(suffix) if suffix else 0


def _references_by_part(design: BoardDesign) -> dict[str, list[str]]:
    """Group only board-fitted references by approved product identity."""
    references: dict[str, list[str]] = defaultdict(list)
    for component in design.components.values():
        references[component.spec.part_key].append(component.reference)
    return references


def render(design: BoardDesign | None = None) -> str:
    design = design or board_definition.load()
    references = _references_by_part(design)
    for key in EXTRA_ASSEMBLY_PARTS:
        references[key].append("—")

    rows = []
    for key in sorted(references):
        spec = COMPONENTS[key]
        refs = sorted(references[key], key=reference_sort_key)
        rows.append(
            f"| {len(refs)} | `{spec.mpn}` | {spec.manufacturer} | "
            f"{spec.description} | {spec.package} | {', '.join(refs)} |"
        )

    text = [
        "# Approved bill of materials",
        "",
        "Generated from `hardware/shared/components.py` and `netlist.json`.",
        "Every row names an exact manufacturer part number; substitutions require",
        "updating the shared catalog and passing footprint/package validation.",
        "",
        "| Qty | Manufacturer part number | Manufacturer | Description | Package | References |",
        "|---:|---|---|---|---|---|",
        *rows,
        "",
    ]
    return "\n".join(text)


def render_assembly_csv(design: BoardDesign | None = None) -> str:
    """Render a PCBWay-friendly BOM containing board-fitted parts only."""
    design = design or board_definition.load()
    references = _references_by_part(design)

    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        ("Item", "Quantity", "Reference", "Value", "Footprint", "Manufacturer", "MPN")
    )
    for item, key in enumerate(sorted(references), 1):
        spec = COMPONENTS[key]
        refs = sorted(references[key], key=reference_sort_key)
        writer.writerow(
            (
                item,
                len(refs),
                ",".join(refs),
                spec.description,
                spec.package,
                spec.manufacturer,
                spec.mpn,
            )
        )
    return output.getvalue()


def write() -> None:
    artifacts.GENERATED_DIR.mkdir(exist_ok=True)
    design = board_definition.load()
    artifacts.BOM.write_text(render(design))
    artifacts.ASSEMBLY_BOM.write_text(render_assembly_csv(design))


if __name__ == "__main__":
    write()
