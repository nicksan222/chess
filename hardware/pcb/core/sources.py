"""Read the two upstream domains without importing either as a package.

This domain needs the mechanical envelope from `hardware/cad` and the wiring
assignment from `hardware/electronics`. It must not copy either set of numbers,
because a third copy is a third thing to keep in step.

Direct imports are not available: both domains contain a package called `core`,
so putting both roots on the path would make one shadow the other. Loading the
two modules by file path under distinct names avoids that entirely, and has the
side benefit of making the dependency explicit and auditable — these are the only
two files this domain reads from elsewhere, plus one generated artefact.

Neither module pulls in a heavy dependency: the CAD dimensions import only
`math`, and the electronics names module imports nothing. So this domain's
toolchain needs Gerbonara and nothing else.
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

CAD_DIMENSIONS_PATH = HARDWARE_ROOT / "cad" / "core" / "dimensions.py"
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
    return _load(CAD_DIMENSIONS_PATH, "pcb_cad_dimensions")


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
