"""The handwritten firmware Hall-bank table must match the shared bank contract."""

import re
import unittest
from pathlib import Path

from shared.dimensions.board import HALL_BANKS

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "apps/firmware/src/hardware/hall/bank.rs"


def firmware_banks(source: str) -> tuple[int, list[list[str]]]:
    """The first address and each bank's squares in channel order."""
    address = re.search(r"pub const FIRST_ADDRESS: u8 = (0x[0-9A-Fa-f]+|\d+);", source)
    if address is None:
        raise ValueError("FIRST_ADDRESS is missing")
    table = re.search(r"= banks!\[(.*?)\];", source, re.DOTALL)
    if table is None:
        raise ValueError("banks! table is missing")
    rows: list[str] = re.findall(r"^\s*\[([^\]]*)\]", table[1], re.MULTILINE)
    squares: list[list[str]] = [re.findall(r"[A-H][1-8]", row) for row in rows]
    return int(address[1], 0), squares


class FirmwareHallBanksTest(unittest.TestCase):
    def test_firmware_matches_bank_addresses_and_channel_squares(self) -> None:
        first_address, rows = firmware_banks(SOURCE.read_text())
        self.assertEqual(
            [first_address + index for index in range(len(rows))],
            [bank.address for bank in HALL_BANKS],
        )
        self.assertEqual(
            rows,
            [[square.name for square in bank.members] for bank in HALL_BANKS],
        )

    def test_parser_reads_rows_and_ignores_the_channel_header(self) -> None:
        source = (
            "pub const FIRST_ADDRESS: u8 = 0x38;\n"
            "const BANKS: X = banks![\n"
            "    //P0 P1\n"
            "    [A1, B1],\n"
            "    [C3, D4],\n"
            "];"
        )
        self.assertEqual(firmware_banks(source), (0x38, [["A1", "B1"], ["C3", "D4"]]))
        with self.assertRaisesRegex(ValueError, "FIRST_ADDRESS"):
            firmware_banks("banks![[A1]];")


if __name__ == "__main__":
    unittest.main()
