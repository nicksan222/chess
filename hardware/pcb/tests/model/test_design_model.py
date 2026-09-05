"""The complete board is one typed, navigable domain object graph."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

from board import definition as board_definition
from board.wiring.nets import Net
from components.capacitor import Capacitor, CapacitorPin
from components.hall_sensor import HallSensor, HallSensorPin
from domain.connectivity import CircuitBuilder


class BoardDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = board_definition.load()

    def test_design_composes_every_component_once(self) -> None:
        self.assertEqual(len(self.design.components), len(self.design.placements))
        self.assertEqual(
            set(self.design.components),
            {placement.reference for placement in self.design.placements},
        )

    def test_component_instance_owns_model_spec_placement_and_pins(self) -> None:
        hall = self.design.component("HS1")
        self.assertEqual(hall.reference, "HS1")
        self.assertEqual(hall.spec.part_key, "HALL_SENSOR")
        self.assertEqual(hall.placement.reference, hall.reference)
        self.assertEqual(
            {pin.definition for pin in hall.pins},
            set(HallSensorPin),
        )

    def test_pin_resolves_net_and_connected_peers(self) -> None:
        output = self.design.pin("HS1", HallSensorPin.ACTIVE_LOW_OUTPUT)
        self.assertEqual(output.net_name(self.design.connections), "SQ_A1")
        peers = output.peers(self.design.connections)
        self.assertEqual(len(peers), 1)
        self.assertTrue(peers[0].reference.startswith("U"))

    def test_pin_relationship_is_navigable_without_pcbnew(self) -> None:
        supply = self.design.pin("HS1", HallSensorPin.SUPPLY)
        bypass = self.design.pin(
            "C72",
            CapacitorPin.SUPPLY_OR_ELECTRODE_A,
        )
        self.assertTrue(supply.is_attached_to(bypass, self.design.connections))
        self.assertEqual(
            supply.net_name(self.design.connections), Net.THREE_VOLTS_THREE
        )

    def test_unknown_component_and_pin_have_contextual_errors(self) -> None:
        with self.assertRaisesRegex(KeyError, "board has no component"):
            self.design.component("NOPE")
        with self.assertRaisesRegex(KeyError, "HS1 has no logical pin"):
            self.design.pin("HS1", "99")


class CircuitBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sensor = HallSensor("HS_TEST")
        self.capacitor = Capacitor("C_TEST")

    def test_pins_can_attach_themselves_through_a_checked_builder(self) -> None:
        sensor_supply = self.sensor.pin(HallSensorPin.SUPPLY)
        capacitor_supply = self.capacitor.pin(CapacitorPin.SUPPLY_OR_ELECTRODE_A)
        builder = CircuitBuilder()
        sensor_supply.connect(capacitor_supply, using=builder, name="SUPPLY")
        graph = builder.build()

        self.assertTrue(sensor_supply.is_attached_to(capacitor_supply, graph))
        self.assertEqual(sensor_supply.net_name(graph), "SUPPLY")

    def test_a_pin_cannot_be_attached_twice(self) -> None:
        pin = self.sensor.pin(HallSensorPin.SUPPLY)
        builder = CircuitBuilder().connect(pin, name="FIRST")
        with self.assertRaisesRegex(ValueError, "already attached"):
            builder.connect(pin, name="SECOND")


if __name__ == "__main__":
    unittest.main()
