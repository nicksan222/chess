#!/usr/bin/env python3
"""Write the purchasing BOM from approved product identities."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import sys

PCB = Path(__file__).resolve().parent
HARDWARE = PCB.parent
sys.path.insert(0, str(HARDWARE))

from shared.components import COMPONENTS  # noqa: E402

EXTRA_ASSEMBLY_PARTS = (
    "FUSE_5A",
    "PI_ZERO_2_W",
    "OLED_MODULE",
    "POWER_SUPPLY",
    "MICRO_SD",
)


def write() -> None:
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
        refs = sorted(references[key], key=lambda value: (value[:1], int(value[1:]) if value[1:].isdigit() else 0))
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
    (PCB / "design/bom.md").write_text("\n".join(text))


if __name__ == "__main__":
    write()
