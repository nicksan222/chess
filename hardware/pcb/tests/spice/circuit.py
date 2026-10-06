"""Python circuit builder and CI-safe ngspice runner.

Role: `SpiceCircuit` holds a title, netlist rows, control lines and named result windows,
and renders them into a circuit that asserts for itself (a failed bound makes ngspice
exit non-zero). `SpiceRunner` executes it with the system ngspice and returns the printed
`result_*` values; a missing ngspice is an error, not a skip.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SpiceCircuit:
    """A self-asserting SPICE circuit.

    Expectations are rendered as ngspice control-language assertions. A failed
    bound calls ``quit 1``, making the generated circuit independently executable
    and allowing CI to trust ngspice's process status.
    """

    title: str
    rows: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    expectations: dict[str, tuple[float, float]] = field(default_factory=dict)

    def clear_expectations(self) -> SpiceCircuit:
        """Replace generator defaults with a test's explicit check registry."""
        self.expectations.clear()
        return self

    def expect(self, name: str, minimum: float, maximum: float) -> SpiceCircuit:
        """Add a named assertion that a printed result lies in [minimum, maximum].

        Duplicate names are rejected so one result cannot be checked against two windows by mistake.
        """
        key = f"result_{name}"
        if key in self.expectations:
            raise ValueError(f"duplicate SPICE expectation {name}")
        self.expectations[key] = (minimum, maximum)
        return self

    def render(self) -> str:
        """The full netlist: components, then a `.control` block that runs the analysis and exits
        non-zero (`quit 1`) when any expectation fails, so ngspice itself reports the failure.
        """
        controls = [".control", "run", *self.controls]
        for name, (minimum, maximum) in self.expectations.items():
            controls.extend(
                (
                    f"if {name} < {minimum:g}",
                    f'echo "ASSERTION FAILED: {name} below {minimum:g}"',
                    "quit 1",
                    "end",
                    f"if {name} > {maximum:g}",
                    f'echo "ASSERTION FAILED: {name} above {maximum:g}"',
                    "quit 1",
                    "end",
                )
            )
        controls.extend(("quit 0", ".endc", ".end", ""))
        return "\n".join((self.title, *self.rows, *controls))

    def write(self, path: Path) -> Path:
        """Write the rendered circuit to `path` and return it."""
        path.write_text(self.render())
        return path


class SpiceRunner:
    """Execute self-asserting circuits with the system ngspice binary."""

    def __init__(self, executable: str = "ngspice") -> None:
        resolved = shutil.which(executable)
        if resolved is None:
            raise RuntimeError(f"{executable} is required for PCB electrical tests")
        self._executable = resolved

    def run(self, circuit: Path | SpiceCircuit) -> dict[str, float]:
        """Run one circuit; assertion failures are reported by ngspice itself.

        Returns every `result_*` value the deck printed (`print result_x`).
        """
        if isinstance(circuit, SpiceCircuit):
            with tempfile.TemporaryDirectory(
                prefix="chess-spice-circuit-"
            ) as directory:
                return self.run(circuit.write(Path(directory) / "test.cir"))
        process = subprocess.run(
            (self._executable, "-b", circuit.name),
            cwd=circuit.parent,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = process.stdout + process.stderr
        failed = ("Error:", "failed!", "simulation(s) aborted")
        if process.returncode != 0 or any(text in output for text in failed):
            raise AssertionError(f"{circuit}: ngspice failed\n{output}")
        found: list[tuple[str, str]] = re.findall(
            r"^(result_\w+) = (\S+)$", output, re.MULTILINE
        )
        return {name: float(value) for name, value in found}
