"""Read shared contracts and the schematic's generated netlist.

The shared package deliberately has no CAD, EDA, or PCB dependency, so future
KiCad and other domain adapters can consume the same definitions.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
REPOSITORY_ROOT = HARDWARE_ROOT.parent

NETLIST_PATH = HARDWARE_ROOT / "electronics" / "generated" / "netlist.json"

PROJECT_NAME = "board"


def _shared(module: str) -> ModuleType:
    if str(HARDWARE_ROOT) not in sys.path:
        sys.path.insert(0, str(HARDWARE_ROOT))
    return importlib.import_module(f"shared.{module}")


def dimensions() -> ModuleType:
    """The shared mechanical envelope and feature positions."""
    return _shared("dimensions")


def names() -> ModuleType:
    """The shared wiring assignment, net names, and host lines."""
    return _shared("wiring")


def netlist() -> dict:
    """The published schematic connectivity for the board project."""
    if not NETLIST_PATH.is_file():
        raise RuntimeError(
            f"{NETLIST_PATH} is missing. Run ./tools/electronics first; the "
            "schematic publishes the netlist this domain consumes."
        )
    published = json.loads(NETLIST_PATH.read_text())
    if published.get("schema") != 1:
        raise RuntimeError(f"Unsupported netlist schema {published.get('schema')}")
    projects = published["projects"]
    if PROJECT_NAME not in projects:
        raise RuntimeError(f"Netlist has no {PROJECT_NAME!r} project")
    return projects[PROJECT_NAME]
