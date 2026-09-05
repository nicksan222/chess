"""Firmware pin markers are projected from pcbnew without board semantics."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PCB_ROOT = Path(__file__).resolve().parents[2]
if str(PCB_ROOT) not in sys.path:
    sys.path.insert(0, str(PCB_ROOT))

try:
    import pcbnew
except ModuleNotFoundError:
    pcbnew = None

if pcbnew is not None:
    import generate_firmware_pins
    from generate_firmware_pins import OUTPUT_PATH, connected_pins, render


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class FirmwarePinsTest(unittest.TestCase):
    def test_checked_in_rust_matches_the_native_board(self) -> None:
        self.assertEqual(OUTPUT_PATH.read_text(), render())

    def test_writer_and_check_modes_use_actual_pcbnew_connectivity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pins.rs"
            with patch.object(generate_firmware_pins, "OUTPUT_PATH", output):
                with patch.object(sys, "argv", ["generate_firmware_pins"]):
                    generate_firmware_pins.main()
                self.assertEqual(output.read_text(), render())
                with patch.object(sys, "argv", ["generate_firmware_pins", "--check"]):
                    generate_firmware_pins.main()
                    output.write_text("stale")
                    with self.assertRaisesRegex(SystemExit, "justfile pins"):
                        generate_firmware_pins.main()
                    self.assertEqual(output.read_text(), "stale")

    def test_every_generated_gpio_has_one_host_header_position(self) -> None:
        pins = connected_pins()
        self.assertEqual(len(pins), 16)
        self.assertNotIn(4, {pin.bcm for pin in pins})
        self.assertEqual(len({pin.bcm for pin in pins}), len(pins))
        self.assertEqual(len({pin.header_pin for pin in pins}), len(pins))


if __name__ == "__main__":
    unittest.main()
