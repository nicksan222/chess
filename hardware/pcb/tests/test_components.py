"""Semantic component models keep routing free of anonymous pin strings."""

from __future__ import annotations

import sys
import unittest
from enum import StrEnum
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from components.barrel_jack import BarrelJackPin, DC_INPUT_JACK  # noqa: E402
from components.base import ComponentReference  # noqa: E402
from components.fuse_holder import FuseHolderPin, INPUT_FUSE  # noqa: E402
from components.sk9822 import Sk9822, Sk9822Pin  # noqa: E402


class ComponentModelTest(unittest.TestCase):
    def test_power_endpoints_have_semantic_reference_and_pin_enums(self) -> None:
        reference, pin = DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE)
        self.assertIs(reference, ComponentReference.DC_INPUT_JACK)
        self.assertIs(pin, BarrelJackPin.CENTRE_POSITIVE)

        reference, pin = INPUT_FUSE.endpoint(FuseHolderPin.UNFUSED_INPUT)
        self.assertIs(reference, ComponentReference.INPUT_FUSE)
        self.assertIs(pin, FuseHolderPin.UNFUSED_INPUT)

    def test_get_pins_returns_enums(self) -> None:
        self.assertEqual(
            INPUT_FUSE.get_pins(),
            (FuseHolderPin.UNFUSED_INPUT, FuseHolderPin.FUSED_OUTPUT),
        )
        self.assertTrue(all(isinstance(pin, StrEnum) for pin in INPUT_FUSE.get_pins()))

    def test_a_component_rejects_another_components_pin_enum(self) -> None:
        with self.assertRaises(TypeError):
            INPUT_FUSE.endpoint(BarrelJackPin.CENTRE_POSITIVE)  # type: ignore[arg-type]

    def test_led_chain_directions_are_named(self) -> None:
        self.assertEqual(
            Sk9822.input_pins(),
            frozenset((Sk9822Pin.DATA_IN, Sk9822Pin.CLOCK_IN)),
        )
        self.assertEqual(
            Sk9822.output_pins(),
            frozenset((Sk9822Pin.DATA_OUT, Sk9822Pin.CLOCK_OUT)),
        )


if __name__ == "__main__":
    unittest.main()
