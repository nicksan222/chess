"""Netlist topology checks against the Schemdraw model."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ELECTRONICS = Path(__file__).resolve().parents[1]
if str(ELECTRONICS) not in sys.path:
    sys.path.insert(0, str(ELECTRONICS))

PROJECTS = ELECTRONICS / "projects"
SQUARES = [f"{file_}{rank}" for file_ in "ABCDEFGH" for rank in range(1, 9)]

from components.i2c_expander import (
    ADDRESS_PINS,
    INTA_PIN,
    PORT_PINS,
    SCL_PIN as EXPANDER_SCL_PIN,
    SDA_PIN as EXPANDER_SDA_PIN,
)
from components.level_buffer import SPARE_CHANNELS, USED_CHANNELS
from components.pi_header import GPIO_TO_PIN
from components.sk9822 import (
    CLOCK_IN_PIN,
    CLOCK_OUT_PIN,
    DATA_IN_PIN,
    DATA_OUT_PIN,
)
from core.names import (
    BUTTON_GPIO,
    BUTTON_NAMES,
    EXPANDER_COUNT,
    LED_CLOCK_NET,
    LED_DATA_NET,
    SCL_GPIO,
    SCL_NET,
    SDA_GPIO,
    SDA_NET,
    SENSE_IRQ_GPIO,
    SENSE_IRQ_NET,
    SPI_CLOCK_GPIO,
    SPI_CLOCK_NET,
    SPI_DATA_GPIO,
    SPI_DATA_NET,
    button_net,
    expander_of,
    expander_straps,
    sense_net,
)

FIRST_LED = 6
LED_COUNT = 64


def load_board():
    path = PROJECTS / "board" / "generate.py"
    spec = importlib.util.spec_from_file_location("electronics_board_netlist", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.assemble()


class NetlistTopologyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sch = load_board()
        cls.nets = cls.sch.nets()
        cls.circuits = cls.sch.equivalence()

    def test_every_square_reads_one_reed_on_one_expander_pin(self) -> None:
        for rank in range(8):
            for file_index in range(8):
                name = f"{'ABCDEFGH'[file_index]}{rank + 1}"
                nodes = self.nets[sense_net(name)]
                reeds = {ref for ref, _pin in nodes if ref.startswith("RS")}
                index, pin = expander_of(file_index, rank)
                expected = (f"U{index + 1}", PORT_PINS[pin])
                with self.subTest(square=name):
                    self.assertEqual(len(reeds), 1)
                    self.assertIn(expected, nodes)
                    # Exactly one expander pin, or two squares would read as one.
                    self.assertEqual(
                        len({(r, p) for r, p in nodes if r.startswith("U")}), 1
                    )

    def test_no_isolation_diodes_are_needed(self) -> None:
        """Direct inputs are what removes the 64 diodes a matrix would need."""
        libs = {spec.lib for spec in self.sch.symbols}
        self.assertNotIn("DIODE", libs)

    def test_expander_address_straps_are_drawn(self) -> None:
        for index in range(EXPANDER_COUNT):
            expander = f"U{index + 1}"
            for pin, high in zip(ADDRESS_PINS, expander_straps(index)):
                with self.subTest(expander=expander, pin=pin):
                    self.assertEqual(
                        self.sch.net_of(expander, pin), "+3V3" if high else "GND"
                    )

    def test_i2c_bus_reaches_every_device_and_is_pulled_up(self) -> None:
        for net, pin in ((SDA_NET, EXPANDER_SDA_PIN), (SCL_NET, EXPANDER_SCL_PIN)):
            members = {ref for ref, _pin in self.nets[net]}
            with self.subTest(net=net):
                self.assertIn("J1", members, "the Pi drives the bus")
                self.assertIn("J2", members, "the display shares the bus")
                for index in range(EXPANDER_COUNT):
                    self.assertIn(f"U{index + 1}", members)
                    self.assertEqual(self.sch.net_of(f"U{index + 1}", pin), net)
                self.assertTrue(
                    any(ref.startswith("R") for ref, _pin in self.nets[net]),
                    "bus needs an external pull-up",
                )

    def test_sensor_interrupts_are_wired_or_onto_one_line(self) -> None:
        nodes = self.nets[SENSE_IRQ_NET]
        self.assertIn(("J1", GPIO_TO_PIN[SENSE_IRQ_GPIO]), nodes)
        for index in range(EXPANDER_COUNT):
            self.assertIn((f"U{index + 1}", INTA_PIN), nodes)

    def test_pi_carries_the_bus_and_spi_on_its_documented_lines(self) -> None:
        for gpio, net in (
            (SDA_GPIO, SDA_NET),
            (SCL_GPIO, SCL_NET),
            (SPI_DATA_GPIO, SPI_DATA_NET),
            (SPI_CLOCK_GPIO, SPI_CLOCK_NET),
            (SENSE_IRQ_GPIO, SENSE_IRQ_NET),
        ):
            with self.subTest(gpio=gpio):
                self.assertEqual(self.sch.net_of("J1", GPIO_TO_PIN[gpio]), net)

    def test_led_chain_is_continuous_for_both_signals(self) -> None:
        for index in range(LED_COUNT - 1):
            source, target = f"U{FIRST_LED + index}", f"U{FIRST_LED + index + 1}"
            with self.subTest(link=index + 1):
                self.assertEqual(
                    self.circuits[(source, DATA_OUT_PIN)],
                    self.circuits[(target, DATA_IN_PIN)],
                )
                self.assertEqual(
                    self.circuits[(source, CLOCK_OUT_PIN)],
                    self.circuits[(target, CLOCK_IN_PIN)],
                )

    def test_led_chain_links_stay_separate(self) -> None:
        """Continuity is not enough: a chain shorted end to end also passes."""
        links = {
            self.circuits[(f"U{FIRST_LED + index}", DATA_OUT_PIN)]
            for index in range(LED_COUNT - 1)
        }
        self.assertEqual(len(links), LED_COUNT - 1)

    def test_chain_head_is_fed_from_the_buffer_not_the_pi(self) -> None:
        head = f"U{FIRST_LED}"
        self.assertEqual(self.sch.net_of(head, DATA_IN_PIN), LED_DATA_NET)
        self.assertEqual(self.sch.net_of(head, CLOCK_IN_PIN), LED_CLOCK_NET)
        # Both signals cross the 3.3 V to 5 V boundary through U5.
        for (input_net, output_net), (_oe, input_pin, output_pin) in zip(
            ((SPI_DATA_NET, LED_DATA_NET), (SPI_CLOCK_NET, LED_CLOCK_NET)),
            USED_CHANNELS,
        ):
            self.assertEqual(self.sch.net_of("U5", input_pin), input_net)
            self.assertEqual(self.sch.net_of("U5", output_pin), output_net)

    def test_used_buffer_channels_are_enabled_and_spares_are_tied_off(self) -> None:
        for enable_pin, _input_pin, _output_pin in USED_CHANNELS:
            # Output enable is active low.
            self.assertEqual(self.sch.net_of("U5", enable_pin), "GND")
        for enable_pin, input_pin, _output_pin in SPARE_CHANNELS:
            self.assertEqual(self.sch.net_of("U5", enable_pin), "+5V")
            self.assertEqual(self.sch.net_of("U5", input_pin), "GND")

    def test_every_led_is_on_the_five_volt_rail(self) -> None:
        for index in range(LED_COUNT):
            self.assertIn((f"U{FIRST_LED + index}", "1"), self.nets["+5V"])

    def test_every_button_reaches_its_own_pi_line_and_ground(self) -> None:
        seen: set[str] = set()
        for index, name in enumerate(BUTTON_NAMES):
            reference = f"SW{index + 1}"
            net = button_net(name)
            with self.subTest(button=name):
                self.assertEqual(self.sch.net_of(reference, "1"), net)
                self.assertEqual(self.sch.net_of(reference, "2"), "GND")
                self.assertEqual(
                    self.sch.net_of("J1", GPIO_TO_PIN[BUTTON_GPIO[name]]), net
                )
                self.assertNotIn(net, seen)
                seen.add(net)

    def test_power_runs_jack_through_fuse_and_switch_to_the_rail(self) -> None:
        self.assertTrue(self.sch.connected(("J3", "1"), ("F1", "1")))
        self.assertTrue(self.sch.connected(("F1", "2"), ("SW13", "1")))
        self.assertEqual(self.sch.net_of("SW13", "2"), "+5V")
        self.assertEqual(self.sch.net_of("J3", "2"), "GND")
        # The clamp sits across the rail so a bad supply opens the fuse.
        self.assertEqual(self.sch.net_of("D1", "2"), "GND")

    def test_the_board_carries_no_regulator(self) -> None:
        """3.3 V comes off the Pi header, so nothing here converts voltage."""
        values = {spec.value for spec in self.sch.symbols}
        for absent in ("D36V50F5", "AP2112K-3.3", "CH224K", "PCA9306"):
            self.assertNotIn(absent, values)
        self.assertIn("+3V3", self.nets)
        self.assertIn(("J1", "1"), self.nets["+3V3"])

    def test_every_square_is_in_the_export(self) -> None:
        squares = {
            spec.extras["Square"]
            for spec in self.sch.symbols
            if "Square" in spec.extras
        }
        self.assertEqual(squares, set(SQUARES))


if __name__ == "__main__":
    unittest.main()
