"""Control groups share their positions with the real PCB switches."""

import unittest

from shared import dimensions
from shared.panel_buttons import PANEL_BUTTONS


class ControlLayoutTest(unittest.TestCase):
    def test_directions_form_a_cross(self) -> None:
        up, down, left, right = (
            PANEL_BUTTONS.by_name(name) for name in ("UP", "DOWN", "LEFT", "RIGHT")
        )
        self.assertEqual(up.x_mm, down.x_mm)
        self.assertEqual(left.y_mm, right.y_mm)
        self.assertLess(left.x_mm, up.x_mm)
        self.assertGreater(right.x_mm, up.x_mm)
        self.assertGreater(up.y_mm, left.y_mm)
        self.assertLess(down.y_mm, left.y_mm)

    def test_functions_and_reset_are_separate_from_navigation(self) -> None:
        directions = [
            PANEL_BUTTONS.by_name(name) for name in ("UP", "DOWN", "LEFT", "RIGHT")
        ]
        functions = [PANEL_BUTTONS.by_name(f"F{index}") for index in range(1, 6)]
        self.assertLess(
            max(button.x_mm for button in directions),
            min(button.x_mm for button in functions),
        )
        self.assertGreater(
            PANEL_BUTTONS.by_name("RESET").x_mm,
            max(button.x_mm for button in functions),
        )
        self.assertLess(
            PANEL_BUTTONS.by_name("OK").x_mm, dimensions.PANEL_OLED_CENTER_MM[0]
        )

    def test_display_harness_reaches_the_centered_module_with_slack(self) -> None:
        from math import dist

        from shared.components.harness import OLED_WIRE_LENGTH_MM

        connector = dimensions.PCB_STRIP_PLACEMENTS["J2"].centre_mm
        self.assertGreaterEqual(
            OLED_WIRE_LENGTH_MM, dist(connector, dimensions.PANEL_OLED_CENTER_MM) + 30
        )

    def test_oled_routes_end_on_the_supplier_solder_pads(self) -> None:
        from cad.board.board import Board
        from cad.board.wiring import wire_route
        from shared.electronics.harness import OLED_HARNESS

        board = Board()
        expected = (
            (-33.5, -193.81, 26.5),
            (-33.5, -191.27, 26.5),
            (-33.5, -188.73, 26.5),
            (-33.5, -186.19, 26.5),
        )
        for wire, endpoint in zip(OLED_HARNESS, expected):
            with self.subTest(cavity=wire.cavity):
                for actual, wanted in zip(
                    wire_route(wire, board.pcb_definition)[-1], endpoint
                ):
                    self.assertAlmostEqual(actual, wanted)

    def test_switches_clear_the_mounting_supports(self) -> None:
        from math import dist

        clearance = (
            dimensions.PCB_SUPPORT_BOSS_DIAMETER_MM / 2
            + max(dimensions.PANEL_BUTTON_BODY_MM[:2]) / 2
        )
        for button in PANEL_BUTTONS:
            for support in dimensions.PCB_SUPPORT_POSITIONS_MM:
                with self.subTest(button=button.name, support=support):
                    self.assertGreater(dist(button.position_mm, support), clearance)
