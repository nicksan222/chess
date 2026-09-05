"""Physical pin ordering and stable UUIDs join symbol templates to instances."""

import unittest
import uuid

from domain.schematic_symbols import (
    ROOT_UUID,
    instance_lines,
    library_symbol_lines,
    render_symbol_library,
    uid,
)
from shared.components import ComponentSpec


class SchematicSymbolsTest(unittest.TestCase):
    def test_library_symbol_keeps_physical_pin_order_and_offsets(self):
        # Physical numbering need not be sorted or contiguous.
        lines = library_symbol_lines("J9", ["3", "1"], [-1.27, 1.27])
        rendered = "\n".join(lines)
        self.assertIn('(symbol "Generated:J9"', rendered)
        self.assertIn("(rectangle (start -1.27 -2.540) (end 3.81 2.540)", rendered)
        self.assertIn("(pin bidirectional line (at -5.08 -1.270 0)", rendered)
        self.assertIn("(pin bidirectional line (at -5.08 1.270 0)", rendered)
        numbers = [
            line.strip() for line in lines if line.strip().startswith("(number ")
        ]
        self.assertEqual(
            numbers,
            [
                '(number "3" (effects (font (size 1.27 1.27))))',
                '(number "1" (effects (font (size 1.27 1.27))))',
            ],
        )

    def test_instance_keeps_metadata_and_reference_based_pin_identities(self):
        spec = ComponentSpec(
            "TEST",
            "Test connector",
            "TEST-PACKAGE",
            "Maker",
            "MPN-9",
            None,
            "https://example.com/datasheet",
        )
        rendered = "\n".join(instance_lines("J9", spec, ["3", "1"], 25.4, 50.8))
        namespace = uuid.UUID("83abf953-6539-4c7d-9e0f-e3b5ac2c4f3b")
        self.assertEqual(ROOT_UUID, uuid.uuid5(namespace, "root"))
        for name in ("symbol:J9", "pin:J9:0", "pin:J9:1"):
            expected = str(uuid.uuid5(namespace, name))
            self.assertEqual(uid(name), expected)
            self.assertIn(f'(uuid "{expected}")', rendered)
        self.assertLess(rendered.index('(pin "3"'), rendered.index('(pin "1"'))
        self.assertIn("(at 25.400 50.800 0)", rendered)
        for property_name, value in (
            ("Value", spec.mpn),
            ("Datasheet", spec.datasheet),
            ("Description", spec.description),
        ):
            self.assertIn(f'(property "{property_name}" "{value}"', rendered)

    def test_library_extraction_retains_only_embedded_symbols(self):
        symbols = library_symbol_lines("J9", ["1"], [0.0])
        sheet = "\n".join(
            [
                "(kicad_sch",
                "  (lib_symbols",
                *symbols,
                "  )",
                "  (sheet_instances",
                '    (path "/" (page "1"))',
                "  )",
                ")",
            ]
        )
        library = render_symbol_library(sheet)
        self.assertIn("\n".join(line.removeprefix("  ") for line in symbols), library)
        self.assertNotIn("sheet_instances", library)
        self.assertTrue(library.startswith("(kicad_symbol_lib\n"))
        self.assertTrue(library.endswith(")\n"))


if __name__ == "__main__":
    unittest.main()
