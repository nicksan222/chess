"""Read the two upstream domains without importing either as a package.

This domain needs the shared mechanical envelope and the wiring assignment from
`hardware/electronics`. It must not copy either set of numbers, because another
copy is another thing to keep in step.

Modules are loaded by path so the PCB runner remains isolated from sibling
packages named `core`. The shared contract deliberately has no CAD dependency;
future KiCad and other domain adapters consume the same source.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
REPOSITORY_ROOT = HARDWARE_ROOT.parent

SHARED_DIMENSIONS_PATH = HARDWARE_ROOT / "shared" / "dimensions.py"
ELECTRONICS_NAMES_PATH = HARDWARE_ROOT / "electronics" / "core" / "names.py"
NETLIST_PATH = HARDWARE_ROOT / "electronics" / "generated" / "netlist.json"

PROJECT_NAME = "board"


def _load(path: Path, module_name: str) -> ModuleType:
    if not path.is_file():
        raise RuntimeError(f"Upstream source is missing: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def dimensions() -> ModuleType:
    """The mechanical envelope: board size, square pitch, feature positions."""
    return _load(SHARED_DIMENSIONS_PATH, "pcb_shared_dimensions")


def names() -> ModuleType:
    """The wiring assignment: squares to expander pins, buttons to Pi lines."""
    return _load(ELECTRONICS_NAMES_PATH, "pcb_electronics_names")


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
