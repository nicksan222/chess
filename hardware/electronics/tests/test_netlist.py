"""Netlist topology checks against the Schemdraw model."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ELECTRONICS = Path(__file__).resolve().parents[1]
PROJECTS = ELECTRONICS / "projects"
SQUARES = [f"{file_}{rank}" for file_ in "ABCDEFGH" for rank in range(1, 9)]

PICO_PINS = {
    "1": "GP0",
    "2": "GP1",
    "4": "GP2",
    "5": "GP3",
    "6": "GP4",
    "7": "GP5",
    "9": "GP6",
    "10": "GP7",
    "11": "GP8",
    "12": "GP9",
    "14": "GP10",
    "15": "GP11",
    "16": "GP12",
    "17": "GP13",
    "19": "GP14",
    "20": "GP15",
    "21": "GP16",
    "31": "GP26",
}


def load_chessboard():
    path = PROJECTS / "chessboard" / "generate.py"
    spec = importlib.util.spec_from_file_location("electronics_chessboard_netlist", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.assemble()


class NetlistTopologyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sch = load_chessboard()
        cls.nets = cls.sch.nets()

    def test_pico_gpio_assignment(self) -> None:
        self.assertEqual(self.sch.net_of("U2", "1"), "LED_DATA_3V3")
        self.assertEqual(self.sch.net_of("U2", "31"), "BAT_ADC")
        for index in range(8):
            row_pin = ("2", "4", "5", "6", "7", "9", "10", "11")[index]
            col_pin = ("12", "14", "15", "16", "17", "19", "20", "21")[index]
            self.assertEqual(self.sch.net_of("U2", row_pin), f"ROW_{index}")
            self.assertEqual(self.sch.net_of("U2", col_pin), f"COL_{index}")
            self.assertEqual(PICO_PINS[row_pin], f"GP{index + 1}")
            self.assertEqual(PICO_PINS[col_pin], f"GP{index + 9}")

    def test_matrix_has_eight_switches_per_row_and_column(self) -> None:
        for index in range(8):
            row = {ref for ref, _pin in self.nets[f"ROW_{index}"] if ref.startswith("D")}
            col = {ref for ref, _pin in self.nets[f"COL_{index}"] if ref.startswith("SW")}
            self.assertEqual(len(row), 8, f"ROW_{index}")
            self.assertEqual(len(col), 8, f"COL_{index}")
            pull = {ref for ref, _pin in self.nets[f"COL_{index}"] if ref.startswith("R")}
            self.assertEqual(len(pull), 1)

    def test_led_chain_is_64_devices_long(self) -> None:
        self.assertIn(("U2", "1"), self.nets["LED_DATA_3V3"])
        self.assertIn(("U67", "2"), self.nets["LED_DATA_3V3"])
        self.assertIn(("U3", "4"), self.nets["LED_DATA_CHAIN"])
        self.assertIn(("R2", "2"), self.nets["LED_DATA_CHAIN"])
        for index in range(3, 67):
            self.assertIn((f"U{index}", "1"), self.nets["+5V"])
        self.assertTrue(
            any(("U66", "2") in nodes and "LED_DOUT_LAST" in name for name, nodes in self.nets.items())
        )

    def test_every_square_is_in_the_export(self) -> None:
        squares = {
            spec.extras["Square"]
            for spec in self.sch.symbols
            if "Square" in spec.extras
        }
        self.assertEqual(squares, set(SQUARES))


if __name__ == "__main__":
    unittest.main()
