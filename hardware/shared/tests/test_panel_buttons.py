"""Golden tests for the unified control-panel button contract."""

import unittest
from dataclasses import replace

from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin
from shared.panel_buttons import PANEL_BUTTONS


class PanelLayoutTest(unittest.TestCase):
    def test_all_button_records_are_stable(self) -> None:
        expected = (
            ("UP", 5, (0.0, -172.0), "SW1", 11, 0.8, 2),
            ("DOWN", 6, (16.0, -172.0), "SW2", 10, -0.8, 1),
            ("LEFT", 12, (32.0, -172.0), "SW3", 9, 0.8, 0),
            ("RIGHT", 13, (48.0, -172.0), "SW4", 8, -0.8, 2),
            ("OK", 16, (64.0, -172.0), "SW5", 7, 0.8, 1),
            ("RESET", 17, (80.0, -172.0), "SW6", 3, 0.8, 0),
            ("PASS", 19, (0.0, -188.0), "SW7", 4, -0.8, 1),
            ("F1", 20, (16.0, -188.0), "SW8", 5, 0.8, 0),
            ("F2", 21, (32.0, -188.0), "SW9", 6, -0.8, 0),
            ("F3", 22, (48.0, -188.0), "SW10", 0, 0.8, 2),
            ("F4", 23, (64.0, -188.0), "SW11", 1, 0.8, 1),
            ("F5", 24, (80.0, -188.0), "SW12", 2, -0.8, 2),
        )
        actual = tuple(
            (
                button.name,
                button.gpio,
                button.position_mm,
                button.switch_reference,
                button.routing_priority,
                button.header_launch_x_offset_mm,
                button.fallback_layer_index,
            )
            for button in PANEL_BUTTONS
        )

        self.assertEqual(actual, expected)
        self.assertEqual(
            [button.name for button in PANEL_BUTTONS.routing_order],
            [
                "F3",
                "F4",
                "F5",
                "RESET",
                "PASS",
                "F1",
                "F2",
                "OK",
                "RIGHT",
                "LEFT",
                "DOWN",
                "UP",
            ],
        )
        self.assertEqual(
            [button.net_name for button in PANEL_BUTTONS],
            [f"BTN_{record[0]}" for record in expected],
        )

    def test_gpio_follows_typed_header_pin(self) -> None:
        button = replace(
            PANEL_BUTTONS.by_name("UP"),
            header_pin=RaspberryPiHeaderPin.BUTTON_DOWN_GPIO6,
        )
        self.assertEqual(button.gpio, 6)

    def test_button_header_pins_are_explicit(self) -> None:
        expected = (
            RaspberryPiHeaderPin.BUTTON_UP_GPIO5,
            RaspberryPiHeaderPin.BUTTON_DOWN_GPIO6,
            RaspberryPiHeaderPin.BUTTON_LEFT_GPIO12,
            RaspberryPiHeaderPin.BUTTON_RIGHT_GPIO13,
            RaspberryPiHeaderPin.BUTTON_OK_GPIO16,
            RaspberryPiHeaderPin.BUTTON_RESET_GPIO17,
            RaspberryPiHeaderPin.BUTTON_PASS_GPIO19,
            RaspberryPiHeaderPin.BUTTON_F1_GPIO20,
            RaspberryPiHeaderPin.BUTTON_F2_GPIO21,
            RaspberryPiHeaderPin.BUTTON_F3_GPIO22,
            RaspberryPiHeaderPin.BUTTON_F4_GPIO23,
            RaspberryPiHeaderPin.BUTTON_F5_GPIO24,
        )
        self.assertEqual(tuple(button.header_pin for button in PANEL_BUTTONS), expected)
