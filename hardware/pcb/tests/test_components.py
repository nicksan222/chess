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
from components.base import ComponentReference, Endpoint  # noqa: E402
from components.catalog import for_netlist_entry, known_part_keys  # noqa: E402
from components.dip_socket import Dip14Socket, Dip28Socket  # noqa: E402
from components.fuse_holder import FuseHolderPin, INPUT_FUSE  # noqa: E402
from components.mcp23017 import Mcp23017Pin  # noqa: E402
from components.ahct125 import Ahct125Pin  # noqa: E402
from components.sk9822 import Sk9822, Sk9822Pin  # noqa: E402
from core import sources  # noqa: E402
import footprints  # noqa: E402


class ComponentModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.netlist = sources.netlist()

    def test_every_board_product_has_a_component_model(self) -> None:
        used = {
            entry["part_key"] for entry in self.netlist["components"].values()
        }
        self.assertEqual(used - known_part_keys(), set())
        for reference, entry in self.netlist["components"].items():
            with self.subTest(reference=reference):
                self.assertEqual(
                    for_netlist_entry(reference, entry).reference,
                    reference,
                )

    def test_every_footprint_exposes_exactly_its_models_logical_pins(self) -> None:
        for reference, entry in self.netlist["components"].items():
            model = for_netlist_entry(reference, entry)
            footprint = footprints.for_package(entry["package"])
            with self.subTest(reference=reference):
                self.assertEqual(
                    {pad.net_number for pad in footprint.pads},
                    set(model.get_pins()),
                )

    def test_every_serialized_connection_pin_resolves_to_an_enum(self) -> None:
        components = {
            reference: for_netlist_entry(reference, entry)
            for reference, entry in self.netlist["components"].items()
        }
        for connection in self.netlist["connections"]:
            for reference, number in connection["pads"]:
                with self.subTest(reference=reference, number=number):
                    pin = components[reference].get_pin_by_number(number)
                    self.assertIsInstance(pin, StrEnum)

    def test_sockets_expose_the_installed_ics_semantic_pins(self) -> None:
        self.assertIs(Dip28Socket("U1S").get_pin_by_number("12"), Mcp23017Pin.I2C_CLOCK)
        self.assertIs(
            Dip14Socket("U5S").get_pin_by_number("2"),
            Ahct125Pin.BUFFER_1_INPUT,
        )

    def test_power_endpoints_have_semantic_reference_and_pin_enums(self) -> None:
        endpoint = DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE)
        self.assertIsInstance(endpoint, Endpoint)
        reference, pin = endpoint
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
