"""Semantic component models keep routing free of anonymous pin strings."""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from enum import StrEnum
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from components.barrel_jack import BarrelJackPin, DC_INPUT_JACK  # noqa: E402
from components.base import ComponentReference, Endpoint  # noqa: E402
from components.catalog import for_netlist_entry, known_part_keys  # noqa: E402
from components.capacitor import CapacitorPin  # noqa: E402
from components.fuse import FusePin, INPUT_FUSE  # noqa: E402
from components.hall_sensor import HallSensorPin  # noqa: E402
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

    def test_cost_optimized_packages_are_used_consistently(self) -> None:
        components = self.netlist["components"]
        by_key = {}
        for reference, entry in components.items():
            by_key.setdefault(entry["part_key"], []).append((reference, entry))

        self.assertNotIn("DIP14_SOCKET", by_key)
        self.assertNotIn("DIP28_SOCKET", by_key)
        self.assertNotIn("REED_SWITCH", by_key)
        self.assertEqual(len(by_key["HALL_SENSOR"]), 64)
        self.assertEqual(len(by_key["MCP23017"]), 4)
        self.assertTrue(
            all(
                entry["package"] == "SOIC-28W 1.27 mm"
                for _reference, entry in by_key["MCP23017"]
            )
        )
        self.assertEqual(len(by_key["AHCT125"]), 1)
        self.assertEqual(
            by_key["AHCT125"][0][1]["package"],
            "SOIC-14 1.27 mm",
        )
        self.assertTrue(
            all(
                entry["package"] == "0603 (1608 metric)"
                for _reference, entry in by_key["CAP_100N"]
            )
        )
        hall_caps = {
            reference: entry
            for reference, entry in by_key["CAP_100N"]
            if "Sensor" in entry["extras"]
        }
        self.assertEqual(len(hall_caps), 64)
        self.assertEqual(
            {entry["extras"]["Sensor"] for entry in hall_caps.values()},
            {reference for reference, _entry in by_key["HALL_SENSOR"]},
        )
        for entry in hall_caps.values():
            sensor = components[entry["extras"]["Sensor"]]
            self.assertEqual(
                entry["extras"]["Square"],
                sensor["extras"]["Square"],
            )

        expander_caps = {
            entry["extras"].get("For")
            for _reference, entry in by_key["CAP_100N"]
            if "For" in entry["extras"]
        }
        self.assertEqual(expander_caps, {"U1", "U2", "U3", "U4"})

    def test_every_footprint_exposes_exactly_its_models_logical_pins(self) -> None:
        for reference, entry in self.netlist["components"].items():
            model = for_netlist_entry(reference, entry)
            footprint = footprints.for_package(entry["package"])
            with self.subTest(reference=reference):
                self.assertEqual(
                    {pad.net_number for pad in footprint.pads},
                    set(model.get_pins()),
                )

    def test_every_endpoint_belongs_to_exactly_one_connection(self) -> None:
        endpoints = Counter(
            tuple(pad)
            for connection in self.netlist["connections"]
            for pad in connection["pads"]
        )
        duplicates = {
            endpoint: count
            for endpoint, count in endpoints.items()
            if count > 1
        }
        self.assertEqual(duplicates, {})

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

    def test_hall_sensors_are_powered_and_active_low(self) -> None:
        pads_by_net = {
            connection.get("name"): {tuple(pad) for pad in connection["pads"]}
            for connection in self.netlist["connections"]
            if connection.get("name")
        }
        sensors = {
            reference
            for reference, entry in self.netlist["components"].items()
            if entry["part_key"] == "HALL_SENSOR"
        }
        hall_caps = {
            reference
            for reference, entry in self.netlist["components"].items()
            if entry["part_key"] == "CAP_100N"
            and "Sensor" in entry["extras"]
        }
        self.assertEqual(len(sensors), 64)
        self.assertEqual(len(hall_caps), 64)
        for reference in hall_caps:
            self.assertIn(
                (reference, CapacitorPin.SUPPLY_OR_ELECTRODE_A),
                pads_by_net["+3V3"],
            )
            self.assertIn(
                (reference, CapacitorPin.RETURN_OR_ELECTRODE_B),
                pads_by_net["GND"],
            )
        for reference in sensors:
            self.assertIn((reference, HallSensorPin.SUPPLY), pads_by_net["+3V3"])
            self.assertIn((reference, HallSensorPin.GROUND), pads_by_net["GND"])
            square_nets = [
                name
                for name, pads in pads_by_net.items()
                if name.startswith("SQ_")
                and (reference, HallSensorPin.ACTIVE_LOW_OUTPUT) in pads
            ]
            self.assertEqual(len(square_nets), 1)

    def test_datasheet_pinouts_do_not_regress_to_logical_numbering(self) -> None:
        # Same Sky PJ-102A mechanical drawing.
        self.assertEqual(BarrelJackPin.CENTRE_POSITIVE, "1")
        self.assertEqual(BarrelJackPin.SLEEVE_GROUND, "2")
        self.assertEqual(BarrelJackPin.SWITCHED_SLEEVE_GROUND, "3")

        # TI DRV5032 DBZ package pinout.
        self.assertEqual(HallSensorPin.SUPPLY, "1")
        self.assertEqual(HallSensorPin.ACTIVE_LOW_OUTPUT, "2")
        self.assertEqual(HallSensorPin.GROUND, "3")

        # Microchip DS20001952D table 2-1 (SOIC column).
        self.assertEqual(Mcp23017Pin.GPIO_B0, "1")
        self.assertEqual(Mcp23017Pin.INTERRUPT_B, "19")
        self.assertEqual(Mcp23017Pin.INTERRUPT_A, "20")
        self.assertEqual(Mcp23017Pin.GPIO_A7, "28")
        self.assertEqual(Mcp23017Pin.SUPPLY, "9")

        # SK9822 manufacturer specification section 5.
        self.assertEqual(Sk9822Pin.DATA_IN, "1")
        self.assertEqual(Sk9822Pin.CLOCK_IN, "2")
        self.assertEqual(Sk9822Pin.GROUND, "3")
        self.assertEqual(Sk9822Pin.FIVE_VOLTS, "4")
        self.assertEqual(Sk9822Pin.CLOCK_OUT, "5")
        self.assertEqual(Sk9822Pin.DATA_OUT, "6")

    def test_critical_ic_rails_use_datasheet_pins(self) -> None:
        pads_by_net = {
            connection.get("name"): {tuple(pad) for pad in connection["pads"]}
            for connection in self.netlist["connections"]
            if connection.get("name")
        }
        for reference in ("U1", "U2", "U3", "U4"):
            self.assertIn((reference, Mcp23017Pin.SUPPLY), pads_by_net["+3V3"])
            self.assertIn((reference, Mcp23017Pin.GROUND), pads_by_net["GND"])
        self.assertIn(("U5", Ahct125Pin.SUPPLY), pads_by_net["+5V"])
        self.assertIn(("U5", Ahct125Pin.GROUND), pads_by_net["GND"])
        self.assertIn(
            ("J3", BarrelJackPin.SWITCHED_SLEEVE_GROUND), pads_by_net["GND"]
        )

    def test_power_endpoints_have_semantic_reference_and_pin_enums(self) -> None:
        endpoint = DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE)
        self.assertIsInstance(endpoint, Endpoint)
        reference, pin = endpoint
        self.assertIs(reference, ComponentReference.DC_INPUT_JACK)
        self.assertIs(pin, BarrelJackPin.CENTRE_POSITIVE)

        reference, pin = INPUT_FUSE.endpoint(FusePin.UNFUSED_INPUT)
        self.assertIs(reference, ComponentReference.INPUT_FUSE)
        self.assertIs(pin, FusePin.UNFUSED_INPUT)

    def test_get_pins_returns_enums(self) -> None:
        self.assertEqual(
            INPUT_FUSE.get_pins(),
            (FusePin.UNFUSED_INPUT, FusePin.FUSED_OUTPUT),
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
