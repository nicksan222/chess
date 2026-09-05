"""Python circuit builder and CI-safe ngspice runner."""

from __future__ import annotations

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
        key = f"result_{name}"
        if key in self.expectations:
            raise ValueError(f"duplicate SPICE expectation {name}")
        self.expectations[key] = (minimum, maximum)
        return self

    def render(self) -> str:
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
        path.write_text(self.render())
        return path


class SpiceRunner:
    """Execute self-asserting circuits with the system ngspice binary."""

    def __init__(self, executable: str = "ngspice") -> None:
        resolved = shutil.which(executable)
        if resolved is None:
            raise RuntimeError(f"{executable} is required for PCB electrical tests")
        self._executable = resolved

    def run(self, circuit: Path | SpiceCircuit) -> None:
        """Run one circuit; assertion failures are reported by ngspice itself."""
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
        if process.returncode != 0 or "Error:" in output or "failed!" in output:
            raise AssertionError(f"{circuit}: ngspice failed\n{output}")
