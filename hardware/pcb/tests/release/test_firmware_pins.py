"""Firmware pin markers are projected from pcbnew without board semantics."""

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

try:
    import pcbnew
except ModuleNotFoundError:
    pcbnew = None

if pcbnew is not None:
    from generate_firmware_pins import OUTPUT_PATH, connected_pins, render


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class FirmwarePinsTest(unittest.TestCase):
    def test_checked_in_rust_matches_the_native_board(self) -> None:
        self.assertEqual(OUTPUT_PATH.read_text(), render())

    def test_every_generated_gpio_has_one_host_header_position(self) -> None:
        pins = connected_pins()
        self.assertEqual(len(pins), 17)
        self.assertEqual(len({pin.bcm for pin in pins}), len(pins))
        self.assertEqual(len({pin.header_pin for pin in pins}), len(pins))


if __name__ == "__main__":
    unittest.main()
