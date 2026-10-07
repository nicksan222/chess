"""Require KiCad schematic/PCB parity without suppressing ERC or DRC findings."""

import json
from pathlib import Path
from typing import cast


def check_schematic_parity(path: Path) -> None:
    """Reject missing parity results and any mismatch between saved outputs."""
    report = cast(dict[str, object], json.loads(path.read_text()))
    parity = cast(list[object], report["schematic_parity"])
    if parity:
        raise ValueError(f"KiCad reports {len(parity)} schematic/PCB parity findings")


def check_routed_copper(path: Path) -> None:
    """Require the saved board to pass DRC and have no remaining airwires."""
    report = cast(dict[str, object], json.loads(path.read_text()))
    for key in ("violations", "unconnected_items"):
        findings = cast(list[object], report[key])
        if findings:
            raise ValueError(
                f"KiCad reports {len(findings)} {key}: {json.dumps(findings[:3])}"
            )
