"""Executable behavioral SPICE programs for advanced circuit converters.

Typed ``Circuit.check`` remains the API for built-in models. Specialized board
converters can use this lower-level renderer for behavioral devices, transmission
lines and plane meshes. Both paths use the same strict ngspice result parser.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..measurement import Limit
from .number import spice_number
from .run import parse_output


class SimulationUnavailable(RuntimeError):
    """A required physical simulation input has not yet been generated."""


@dataclass
class SpiceProgram:
    """A converter's netlist, analysis commands and mandatory scalar limits."""

    title: str
    rows: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    expectations: dict[str, Limit] = field(default_factory=dict)

    def clear_expectations(self) -> SpiceProgram:
        self.expectations.clear()
        return self

    def expect(self, name: str, minimum: float, maximum: float) -> SpiceProgram:
        key = f"result_{name}"
        if not re.fullmatch(r"result_[a-z0-9_]+", key):
            raise ValueError(f"unsafe SPICE result name: {name}")
        if key in self.expectations:
            raise ValueError(f"duplicate SPICE expectation: {name}")
        self.expectations[key] = Limit(minimum, maximum)
        return self

    def render(self) -> str:
        if not self.expectations:
            raise ValueError("SPICE program needs explicit expectations")
        controls = [".control", "run", *self.controls]
        for name, limit in self.expectations.items():
            minimum, maximum = map(spice_number, (limit.minimum, limit.maximum))
            controls.extend(
                (
                    f"print {name}",
                    f"if {name} < {minimum}",
                    f'echo "ASSERTION FAILED: {name} below {minimum}"',
                    "quit 1",
                    "end",
                    f"if {name} > {maximum}",
                    f'echo "ASSERTION FAILED: {name} above {maximum}"',
                    "quit 1",
                    "end",
                )
            )
        controls.extend(("quit 0", ".endc", ".end", ""))
        return "\n".join((self.title, *self.rows, *controls))

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render())
        return path


def run_program(program: SpiceProgram, path: Path | None = None) -> dict[str, float]:
    """Require successful ngspice execution and every expected measured value."""
    executable = shutil.which("ngspice")
    if executable is None:
        raise RuntimeError("ngspice is required for board electrical tests")
    if path is None:
        with tempfile.TemporaryDirectory(prefix="chess-harness-spice-") as directory:
            return run_program(program, Path(directory) / "scenario.cir")
    # Preserve every executed corner even when a converter requests the same
    # descriptive filename repeatedly. Generation starts with an empty stage.
    base_path = path
    index = 2
    while path.exists():
        path = base_path.with_name(f"{base_path.stem}-{index}{base_path.suffix}")
        index += 1
    program.write(path)
    process = subprocess.run(
        (executable, "-b", path.name),
        cwd=path.parent,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = process.stdout + process.stderr
    path.with_suffix(".log").write_text(output)
    if process.returncode:
        raise ValueError(f"ngspice exited {process.returncode}:\n{output}")
    return parse_output(output, program.expectations)
