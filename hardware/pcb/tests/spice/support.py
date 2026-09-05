"""Shared setup for Python-defined SPICE test cases."""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path

import pcb.definition.board as definition
from spice.board_harness import BoardHarness
from spice.circuit import SpiceCircuit, SpiceRunner

PCB_ROOT = Path(__file__).resolve().parents[2]


def board_circuits() -> BoardHarness:
    """Build the circuit DSL against the current validated board definition."""
    manufacturing = json.loads((PCB_ROOT / "definition/manufacturing.json").read_text())
    numerator, denominator = manufacturing["power"]["led_global_brightness_max"].split(
        "/"
    )
    return BoardHarness(definition.load(), Fraction(int(numerator), int(denominator)))


def run_circuit(test_file: str, circuit: SpiceCircuit) -> None:
    """Render into the review output set, or use a temporary standalone circuit."""
    output = os.environ.get("PCB_SPICE_OUTPUT")
    if output:
        path = Path(output)
        path.mkdir(parents=True, exist_ok=True)
        SpiceRunner().run(
            circuit.write(path / Path(test_file).with_suffix(".cir").name)
        )
    else:
        SpiceRunner().run(circuit)
