"""Golden tests for PCB-owned Hall-bank identities and placement."""

import unittest

from pcb.definition.bank_assemblies import BANK_ASSEMBLIES


class HallBankAssemblyTest(unittest.TestCase):
    def test_all_published_bank_records_are_stable(self) -> None:
        expected = (
            ("A1-D2", 0x20, "U1", "C3", (-80.0, -118.0), (-72.0, -112.0)),
            ("E1-H2", 0x21, "U2", "C4", (80.0, -118.0), (88.0, -112.0)),
            ("A3-D4", 0x22, "U3", "C5", (-80.0, -38.0), (-72.0, -32.0)),
            ("E3-H4", 0x23, "U4", "C6", (80.0, -38.0), (88.0, -32.0)),
            ("A5-D6", 0x24, "U70", "C136", (-80.0, 42.0), (-72.0, 48.0)),
            ("E5-H6", 0x25, "U71", "C137", (80.0, 42.0), (88.0, 48.0)),
            ("A7-D8", 0x26, "U72", "C138", (-80.0, 122.0), (-72.0, 128.0)),
            ("E7-H8", 0x27, "U73", "C139", (80.0, 122.0), (88.0, 128.0)),
        )
        actual = tuple(
            (
                assembly.label,
                assembly.address,
                assembly.expander_reference,
                assembly.bypass_reference,
                assembly.expander_position_mm,
                assembly.bypass_position_mm,
            )
            for assembly in BANK_ASSEMBLIES
        )

        self.assertEqual(actual, expected)
        self.assertEqual(
            [assembly.assembly_name for assembly in BANK_ASSEMBLIES],
            [f"sensing/{record[0]}" for record in expected],
        )

    def test_references_and_positions_are_unique(self) -> None:
        for values in (
            [assembly.address for assembly in BANK_ASSEMBLIES],
            [assembly.expander_reference for assembly in BANK_ASSEMBLIES],
            [assembly.bypass_reference for assembly in BANK_ASSEMBLIES],
            [assembly.expander_position_mm for assembly in BANK_ASSEMBLIES],
            [assembly.bypass_position_mm for assembly in BANK_ASSEMBLIES],
        ):
            self.assertEqual(len(values), len(set(values)))
