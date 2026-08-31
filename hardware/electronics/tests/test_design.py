"""Assignments, names, and the parts catalog."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ELECTRONICS = Path(__file__).resolve().parents[1]
if str(ELECTRONICS) not in sys.path:
    sys.path.insert(0, str(ELECTRONICS))

from components import I2C_EXPANDER, LEVEL_BUFFER, REED, SK9822
from components.i2c_expander import PORT_PINS
from components.pi_header import GPIO_TO_PIN
from core.names import (
    ASSIGNED_GPIO,
    BUTTON_GPIO,
    BUTTON_NAMES,
    EXPANDER_COUNT,
    OLED_ADDRESS,
    expander_address,
    expander_of,
    expander_quadrant,
    expander_squares,
    expander_straps,
    led_chain_order,
    parse_square,
    square,
)


class NamesTest(unittest.TestCase):
    def test_square_round_trip(self) -> None:
        self.assertEqual(square(0, 0), "A1")
        self.assertEqual(square(7, 7), "H8")
        self.assertEqual(parse_square("e4"), (4, 3))

    def test_led_chain_snakes_by_rank_from_a1(self) -> None:
        chain = led_chain_order()
        self.assertEqual(len(chain), 64)
        self.assertEqual(chain[0][0], "A1")
        self.assertEqual(chain[7][0], "H1")
        self.assertEqual(chain[8][0], "H2")
        self.assertEqual(chain[-1][0], "A8")
        self.assertEqual(len({name for name, _f, _r in chain}), 64)


class ExpanderMappingTest(unittest.TestCase):
    def test_every_square_owns_exactly_one_expander_pin(self) -> None:
        """No square may share a pin, or the board would read two at once."""
        taken: dict[tuple[int, int], str] = {}
        for rank in range(8):
            for file_index in range(8):
                key = expander_of(file_index, rank)
                name = square(file_index, rank)
                self.assertNotIn(key, taken, f"{name} collides with {taken.get(key)}")
                taken[key] = name
        self.assertEqual(len(taken), 64)

    def test_each_expander_carries_sixteen_squares(self) -> None:
        for index in range(EXPANDER_COUNT):
            squares = expander_squares(index)
            self.assertEqual(len(squares), 16, index)
            self.assertEqual(sorted(pin for pin, _name in squares), list(range(16)))
            self.assertEqual(len(PORT_PINS), 16)

    def test_quadrants_keep_reed_traces_short(self) -> None:
        """An expander must only serve squares inside its own 4x4 block."""
        self.assertEqual(
            [expander_quadrant(index) for index in range(EXPANDER_COUNT)],
            ["A1-D4", "E1-H4", "A5-D8", "E5-H8"],
        )
        for index in range(EXPANDER_COUNT):
            files = {name[0] for _pin, name in expander_squares(index)}
            ranks = {name[1] for _pin, name in expander_squares(index)}
            self.assertEqual(len(files), 4, index)
            self.assertEqual(len(ranks), 4, index)

    def test_addresses_are_consecutive_and_clear_of_the_display(self) -> None:
        addresses = [expander_address(index) for index in range(EXPANDER_COUNT)]
        self.assertEqual(addresses, [0x20, 0x21, 0x22, 0x23])
        self.assertNotIn(OLED_ADDRESS, addresses)

    def test_address_straps_encode_the_quadrant_index(self) -> None:
        for index in range(EXPANDER_COUNT):
            a0, a1, a2 = expander_straps(index)
            self.assertFalse(a2, "A2 is grounded on every device")
            self.assertEqual(a0 + 2 * a1, index)


class ControlPanelAssignmentTest(unittest.TestCase):
    def test_twelve_buttons_each_have_a_private_line(self) -> None:
        self.assertEqual(len(BUTTON_NAMES), 12)
        self.assertEqual(len(set(BUTTON_GPIO.values())), 12)

    def test_navigation_and_action_buttons_are_all_present(self) -> None:
        self.assertEqual(
            set(BUTTON_NAMES),
            {"UP", "DOWN", "LEFT", "RIGHT", "OK", "RESET", "PASS"}
            | {f"F{n}" for n in range(1, 6)},
        )

    def test_no_pi_line_is_used_twice(self) -> None:
        self.assertEqual(len(ASSIGNED_GPIO), len(set(ASSIGNED_GPIO)))

    def test_every_assigned_line_exists_on_the_header(self) -> None:
        for gpio in ASSIGNED_GPIO:
            self.assertIn(gpio, GPIO_TO_PIN, gpio)

    def test_lines_are_left_spare_for_later(self) -> None:
        spare = set(GPIO_TO_PIN) - set(ASSIGNED_GPIO)
        self.assertGreaterEqual(len(spare), 8)


class CatalogTest(unittest.TestCase):
    def test_the_board_has_exactly_two_integrated_circuit_types(self) -> None:
        self.assertEqual(I2C_EXPANDER.value, "MCP23017-E/SP")
        self.assertEqual(LEVEL_BUFFER.value, "SN74AHCT125N")

    def test_both_integrated_circuits_are_socketed_through_hole(self) -> None:
        """No chip should ever see a soldering iron."""
        self.assertEqual(I2C_EXPANDER.package, "PDIP-28")
        self.assertEqual(LEVEL_BUFFER.package, "DIP-14")

    def test_sensor_and_led_choices_are_the_ones_that_remove_the_mcu(self) -> None:
        self.assertEqual(REED.lib, "REED")
        # A clocked LED is what lets a non-real-time host drive the chain.
        self.assertEqual(SK9822.lib, "SK9822")
        self.assertIn("Clocked", SK9822.description)


if __name__ == "__main__":
    unittest.main()
