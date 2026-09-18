"""Golden tests for the unified control-panel button contract."""

import unittest

from shared.panel import PANEL_BUTTONS


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
