"""The handwritten firmware driver must match the purchased display contract."""

import re
import unittest
from pathlib import Path

from shared import wiring
from shared.components.oled_module import (
    OLED_CONTROLLER,
    OLED_HEIGHT_PIXELS,
    OLED_WIDTH_PIXELS,
)

ROOT = Path(__file__).resolve().parents[3]


def display_contract(source: str) -> tuple[str, int, int, int]:
    controller = re.search(r"^mod (\w+);$", source, re.MULTILINE)
    if controller is None:
        raise ValueError("display controller module is missing")
    values: list[int] = []
    for name in ("WIDTH", "HEIGHT", "I2C_ADDRESS"):
        match = re.search(rf"pub const {name}: u8 = (0x[0-9A-Fa-f]+|\d+);", source)
        if match is None:
            raise ValueError(f"display {name} is missing")
        values.append(int(match[1], 0))
    return controller[1], values[0], values[1], values[2]


class FirmwareDisplayTest(unittest.TestCase):
    def test_firmware_matches_selected_module_and_shared_i2c_address(self) -> None:
        source = (ROOT / "apps/firmware/src/hardware/display/mod.rs").read_text()
        self.assertEqual(
            display_contract(source),
            (
                OLED_CONTROLLER,
                OLED_WIDTH_PIXELS,
                OLED_HEIGHT_PIXELS,
                wiring.OLED_ADDRESS,
            ),
        )

    def test_parser_detects_controller_address_and_geometry_changes(self) -> None:
        source = "mod ssd1306;\npub const WIDTH: u8 = 64;\npub const HEIGHT: u8 = 32;\npub const I2C_ADDRESS: u8 = 0x3D;"
        self.assertEqual(display_contract(source), ("ssd1306", 64, 32, 0x3D))
        with self.assertRaisesRegex(ValueError, "WIDTH"):
            display_contract("mod ssd1309;")
