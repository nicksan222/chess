"""Shared setup for Python-defined SPICE test cases."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from board import definition
from spice.board_harness import BoardHarness
from spice.circuit import SpiceCircuit, SpiceResult, SpiceRunner

PCB_ROOT = Path(__file__).resolve().parents[2]


def board_circuits() -> BoardHarness:
    """Build the circuit DSL against the current validated board definition."""
    manufacturing = json.loads((PCB_ROOT / "board/manufacturing.json").read_text())
    numerator, denominator = manufacturing["power"]["led_global_brightness_max"].split(
        "/"
    )
    return BoardHarness(definition.load(), Fraction(int(numerator), int(denominator)))


def run_circuit(test_file: str, circuit: SpiceCircuit) -> SpiceResult:
    """Render beside its Python case, then execute the matching ``.cir`` file."""
    path = Path(test_file).with_suffix(".cir")
    circuit.write(path)
    return SpiceRunner().run(path)
