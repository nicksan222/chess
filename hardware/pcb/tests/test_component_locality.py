"""Component classes own PCB geometry, routing policy, and rendered labels."""

import unittest
from pathlib import Path

from base import sources
from board import definition
from components.ahct125 import Ahct125
from components.barrel_jack import BarrelJack
from components.capacitor import Capacitor
from components.catalog import for_netlist_entry
from components.fuse import Fuse
from components.hall_sensor import HallSensor
from components.oled_header import OledHeader
from components.power_switch import PowerSwitch
from components.raspberry_pi_header import RaspberryPiHeader
from components.resistor import Resistor
from components.sk9822 import Sk9822
from components.tactile_switch import TactileSwitch
from components.tca9554 import Tca9554
from components.test_point import TestPoint
from components.tvs_diode import TvsDiode
from shared.electronics import (
    Ahct125Component,
    BarrelJackComponent,
    CapacitorComponent,
    FuseComponent,
    HallSensorComponent,
    OledHeaderComponent,
    PowerSwitchComponent,
    RaspberryPiHeaderComponent,
    ResistorComponent,
    Sk9822Component,
    TactileSwitchComponent,
    Tca9554Component,
    TestPointComponent,
    TvsDiodeComponent,
)


class ComponentInheritanceTest(unittest.TestCase):
    def test_every_pcb_component_specializes_its_shared_domain_definition(self):
        pairs = (
            (Ahct125, Ahct125Component),
            (BarrelJack, BarrelJackComponent),
            (Capacitor, CapacitorComponent),
            (Fuse, FuseComponent),
            (HallSensor, HallSensorComponent),
            (OledHeader, OledHeaderComponent),
            (PowerSwitch, PowerSwitchComponent),
            (RaspberryPiHeader, RaspberryPiHeaderComponent),
            (Resistor, ResistorComponent),
            (Sk9822, Sk9822Component),
            (TactileSwitch, TactileSwitchComponent),
            (Tca9554, Tca9554Component),
            (TestPoint, TestPointComponent),
            (TvsDiode, TvsDiodeComponent),
        )
        for pcb_type, shared_type in pairs:
            with self.subTest(component=pcb_type.__name__):
                self.assertTrue(issubclass(pcb_type, shared_type))

    def test_every_placement_uses_its_component_owned_land_pattern(self):
        netlist = sources.netlist()
        design = definition.from_contract(netlist)
        for reference, component in design.components.items():
            with self.subTest(reference=reference):
                model = for_netlist_entry(reference, netlist["components"][reference])
                self.assertIs(
                    component.placement.footprint,
                    model.footprint_for(component.spec.package),
                )

    def test_pi_header_legend_is_derived_locally_and_preserves_board_text(self):
        self.assertEqual(
            RaspberryPiHeader.silkscreen_pinout_lines(),
            (
                "J1 PI: 3 SDA  5 SCL  11 RESET  15 F3",
                "16 F4  18 F5  19 SPI-DATA  23 SPI-CLK",
                "29 UP  31 DOWN  32 LEFT  33 RIGHT  35 PASS  36 OK",
                "38 F1  40 F2 | 1/17 3V3 | 2/4 5V | GND: 6/9/14/20/25/30/34/39",
            ),
        )

    def test_silkscreen_has_no_parallel_pi_pinout_constant(self):
        root = Path(__file__).resolve().parents[1]
        for relative in ("board/wiring/silkscreen.py", "board/wiring/geometry.py"):
            self.assertNotIn("PI_HEADER_PINOUT", (root / relative).read_text())

    def test_component_placement_offsets_are_not_board_dimension_globals(self):
        dimensions = sources.dimensions()
        for name in (
            "LED_BYPASS_OFFSET_MM",
            "HALL_BYPASS_OFFSET_MM",
            "EXPANDER_CAP_OFFSET_MM",
        ):
            self.assertFalse(hasattr(dimensions, name), name)
        self.assertEqual(Capacitor.LED_BYPASS_OFFSET_MM, (0.0, -8.0))
        self.assertEqual(Capacitor.HALL_BYPASS_OFFSET_MM, (0.0, -3.0))
        self.assertEqual(Tca9554.BYPASS_OFFSET_MM, (8.0, 6.0))


if __name__ == "__main__":
    unittest.main()
