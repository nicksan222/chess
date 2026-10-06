"""Tests beside reusable simulation model references."""

import unittest
from enum import StrEnum

from pcb.harness.base.spice.model import ModelParameter, SpiceModel


class Pin(StrEnum):
    A = "1"
    B = "2"


class ModelTest(unittest.TestCase):
    def test_model_requires_distinct_terminals(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            SpiceModel("resistor", (Pin.A, Pin.A))

    def test_model_rejects_duplicate_parameter_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            SpiceModel(
                "resistor",
                (Pin.A, Pin.B),
                (
                    ModelParameter("ohms", 1000.0, "ohm"),
                    ModelParameter("ohms", 2000.0, "ohm"),
                ),
            )

    def test_parameter_rejects_nonfinite_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            ModelParameter("ohms", float("nan"), "ohm")

    def test_model_rejects_empty_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "key"):
            SpiceModel(" ", (Pin.A,))

    def test_model_rejects_non_enum_terminal(self) -> None:
        with self.assertRaisesRegex(ValueError, "terminal"):
            SpiceModel("resistor", ("1",))  # type: ignore[arg-type]
