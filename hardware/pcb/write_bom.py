#!/usr/bin/env python3
"""Write the purchasing BOM from approved product identities."""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

PCB = Path(__file__).resolve().parent
HARDWARE = PCB.parent
sys.path.insert(0, str(HARDWARE))

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


def render() -> str:
    design = json.loads((PCB / "design/netlist.json").read_text())
    components = design["projects"]["board"]["components"]
    references: dict[str, list[str]] = defaultdict(list)
    for reference, component in components.items():
        references[component["part_key"]].append(reference)
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


def render_assembly_csv() -> str:
    """Render a PCBWay-friendly BOM containing board-fitted parts only."""
    design = json.loads((PCB / "design/netlist.json").read_text())
    components = design["projects"]["board"]["components"]
    references: dict[str, list[str]] = defaultdict(list)
    for reference, component in components.items():
        references[component["part_key"]].append(reference)

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
    generated = PCB / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "bom.md").write_text(render())
    (generated / "assembly-bom.csv").write_text(render_assembly_csv())


if __name__ == "__main__":
    write()
