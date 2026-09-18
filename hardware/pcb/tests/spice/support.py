"""Shared setup for Python-defined SPICE test cases."""

from __future__ import annotations

import os
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import cast

import pcb.definition.board as definition
from shared.json_values import parse_json
from spice.board_harness import BoardHarness
from spice.circuit import SpiceCircuit, SpiceRunner

PCB_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ManufacturingSettings:
    led_global_brightness_max: Fraction

    @classmethod
    def load(cls, path: Path) -> ManufacturingSettings:
        document = parse_json(path.read_text())
        if not isinstance(document, dict):
            raise ValueError("manufacturing settings must be an object")
        root = cast(dict[object, object], document)
        power = root.get("power")
        if not isinstance(power, dict):
            raise ValueError("manufacturing power settings must be an object")
        power_fields = cast(dict[object, object], power)
        brightness = power_fields.get("led_global_brightness_max")
        if not isinstance(brightness, str):
            raise ValueError("LED brightness limit must be a fraction")
        return cls(led_global_brightness_max=Fraction(brightness))


def board_circuits() -> BoardHarness:
    """Build the circuit DSL against the current validated board definition."""
    settings = ManufacturingSettings.load(PCB_ROOT / "definition/manufacturing.json")
    return BoardHarness(definition.load(), settings.led_global_brightness_max)


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
