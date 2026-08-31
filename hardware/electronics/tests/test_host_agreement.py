"""The schematic and the host software must agree on the board's wiring.

`core/names.py` decides which expander pin reads which square and where each
square sits in the LED chain. `crates/board-model` has to make the same
decisions, because the host reads bytes off a bus and has to name squares from
them. Nothing in either build would notice the two drifting apart, so this is the
tripwire.

The checks are deliberately about the formulas rather than a table of 64 rows: a
table duplicated in two languages is the thing that rots.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ELECTRONICS = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ELECTRONICS.parents[1]
BOARD_MODEL = REPOSITORY_ROOT / "crates" / "board-model" / "src"

if str(ELECTRONICS) not in sys.path:
    sys.path.insert(0, str(ELECTRONICS))

from core.names import (  # noqa: E402
    EXPANDER_BASE_ADDRESS,
    EXPANDER_COUNT,
    expander_of,
    led_chain_order,
    parse_square,
)


def normalised(text: str) -> str:
    """Collapse whitespace so a line break cannot hide a match."""
    return re.sub(r"\s+", "", text)


class HostMappingAgreementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = normalised((BOARD_MODEL / "mapping.rs").read_text())

    def test_the_host_crate_exists_to_agree_with(self) -> None:
        self.assertTrue((BOARD_MODEL / "mapping.rs").is_file())
        self.assertTrue((BOARD_MODEL / "occupancy.rs").is_file())

    def test_quadrant_formula_matches(self) -> None:
        """Python: (rank // 4) * 2 + (file_index // 4)."""
        self.assertIn(normalised("device: (rank / 4) * 2 + (file / 4)"), self.mapping)

    def test_pin_formula_matches(self) -> None:
        """Python: (rank % 4) * 4 + (file_index % 4)."""
        self.assertIn(normalised("pin: (rank % 4) * 4 + (file % 4)"), self.mapping)

    def test_expander_count_and_base_address_match(self) -> None:
        self.assertIn(
            normalised(f"EXPANDER_COUNT: u8 = {EXPANDER_COUNT}"), self.mapping
        )
        self.assertIn(
            normalised(f"EXPANDER_BASE_ADDRESS: u8 = 0x{EXPANDER_BASE_ADDRESS:02X}"),
            self.mapping,
        )

    def test_the_led_chain_serpentines_on_both_sides(self) -> None:
        chain = led_chain_order()
        # Python reverses the file on odd ranks; Rust must do the same.
        self.assertEqual(chain[0][0], "A1")
        self.assertEqual(chain[8][0], "H2")
        self.assertIn(
            normalised("if rank % 2 == 0 { file } else { 7 - file }"), self.mapping
        )
        self.assertIn(normalised("rank * 8 + along"), self.mapping)

    def test_the_crate_records_which_module_owns_the_assignment(self) -> None:
        """A reader who changes one side needs a pointer to the other."""
        lib = (BOARD_MODEL / "lib.rs").read_text()
        self.assertIn("core/names.py", lib)
        self.assertIn("hardware/electronics", lib)

    def test_port_a_holds_the_lower_ranks_of_each_quadrant(self) -> None:
        """The property the Rust `is_port_b` test asserts, checked here too."""
        for name, (file_index, rank) in (
            (name, parse_square(name)) for name in ("A1", "A3", "E5", "H8")
        ):
            _device, pin = expander_of(file_index, rank)
            with self.subTest(square=name):
                self.assertEqual(pin >= 8, rank % 4 >= 2)


if __name__ == "__main__":
    unittest.main()
