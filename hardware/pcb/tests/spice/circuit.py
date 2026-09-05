"""Python circuit builder and CI-safe ngspice runner."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_MEASURE = re.compile(r"^(result_[A-Za-z0-9_]+)\s*=\s*([-+0-9.eE]+)", re.MULTILINE)


@dataclass
class SpiceCircuit:
    """Builder whose methods each render one readable SPICE row.

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

    def voltage(
        self,
        name: str,
        positive: str,
        value: str | float,
        negative: str = "0",
    ) -> SpiceCircuit:
        self.rows.append(f"V{name} {positive} {negative} {value}")
        return self

    def resistor(
        self, name: str, left: str, right: str, value: str | float
    ) -> SpiceCircuit:
        self.rows.append(f"R{name} {left} {right} {value}")
        return self

    def capacitor(self, name: str, left: str, right: str, value: str) -> SpiceCircuit:
        self.rows.append(f"C{name} {left} {right} {value}")
        return self

    def current(
        self, name: str, positive: str, negative: str, value: str | float
    ) -> SpiceCircuit:
        self.rows.append(f"I{name} {positive} {negative} {value}")
        return self

    def behavioral(
        self, name: str, positive: str, negative: str, expression: str
    ) -> SpiceCircuit:
        self.rows.append(f"B{name} {positive} {negative} {expression}")
        return self

    def switch(
        self, name: str, left: str, right: str, control: str, model: str
    ) -> SpiceCircuit:
        self.rows.append(f"S{name} {left} {right} {control} 0 {model}")
        return self

    def model(self, name: str, kind: str, parameters: str) -> SpiceCircuit:
        self.rows.append(f".model {name} {kind}({parameters})")
        return self

    def raw(self, row: str) -> SpiceCircuit:
        """Add uncommon syntax while retaining one-call-per-row layout."""
        if "\n" in row:
            raise ValueError("a SPICE row cannot contain a newline")
        self.rows.append(row)
        return self

    def control(self, row: str) -> SpiceCircuit:
        if "\n" in row:
            raise ValueError("a SPICE control row cannot contain a newline")
        self.controls.append(row)
        return self

    def transient(self, step: str, stop: str) -> SpiceCircuit:
        self.rows.append(f".tran {step} {stop}")
        return self

    def measure_voltage(self, name: str, node: str, at: str) -> SpiceCircuit:
        self.controls.append(f"meas tran result_{name} FIND v({node}) AT={at}")
        return self

    def measure_current(self, name: str, source: str, at: str) -> SpiceCircuit:
        internal = f"measured_{name}"
        self.controls.append(f"meas tran {internal} FIND i(V{source}) AT={at}")
        self.controls.append(f"let result_{name}=-{internal}")
        self.controls.append(f"print result_{name}")
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


@dataclass(frozen=True)
class SpiceResult:
    """Measurements emitted by one successful circuit simulation."""

    circuit: Path
    measurements: dict[str, float]


class SpiceRunner:
    """Execute self-asserting circuits with the system ngspice binary."""

    def __init__(self, executable: str = "ngspice") -> None:
        resolved = shutil.which(executable)
        if resolved is None:
            raise RuntimeError(f"{executable} is required for PCB electrical tests")
        self._executable = resolved

    def run(self, circuit: Path | SpiceCircuit) -> SpiceResult:
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
        measurements = {name: float(value) for name, value in _MEASURE.findall(output)}
        return SpiceResult(circuit, measurements)
