"""Schematic composition stays reusable while the CLI owns default inputs and I/O."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import write_schematic
from base import schematic
from base.schematic_symbols import render_symbol_library
from board import definition


class SchematicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = definition.load()

    def test_script_defaults_to_the_board_but_accepts_an_explicit_design(self):
        expected = schematic.render(self.design)
        with patch.object(definition, "load", return_value=self.design) as load:
            self.assertEqual(write_schematic.render(), expected)
            load.assert_called_once_with()

        custom = replace(self.design, title="Schematic composition test", revision="T1")
        with patch.object(
            definition, "load", side_effect=AssertionError("unexpected load")
        ):
            rendered = write_schematic.render(custom)
            self.assertEqual(rendered, schematic.render(custom))
        self.assertIn('(title "Schematic composition test")', rendered)
        self.assertIn('(rev "T1")', rendered)

    def test_rendering_retains_every_endpoint_and_is_repeatable(self):
        nets, no_connects = schematic.connectivity(self.design)
        # Several physical switch pads share one logical endpoint. Each physical
        # pin still needs its own schematic label or no-connect marker.
        endpoints = [
            (item.reference, logical)
            for item in self.design.placements
            for logical, _physical, _position, _definition in item.pads()
        ]
        self.assertEqual(set(nets) | no_connects, set(endpoints))
        self.assertFalse(set(nets) & no_connects)
        rendered = schematic.render(self.design)
        self.assertEqual(
            rendered.count("  (global_label "),
            sum(endpoint in nets for endpoint in endpoints),
        )
        self.assertEqual(
            rendered.count("  (no_connect\n"),
            sum(endpoint in no_connects for endpoint in endpoints),
        )
        self.assertEqual(rendered, schematic.render(self.design))

    def test_writer_emits_the_rendered_sheet_library_and_relative_table(self):
        # Redirect only artifact destinations: exercise the real default renderer
        # and writer without touching the repository's reviewed generated files.
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            paths = {
                "GENERATED_DIR": output,
                "SCHEMATIC": output / "chess-board.kicad_sch",
                "SYMBOL_LIBRARY": output / "generated-symbols.kicad_sym",
                "SYMBOL_TABLE": output / "sym-lib-table",
            }
            with (
                patch.multiple(write_schematic.artifacts, **paths),
                redirect_stdout(io.StringIO()),
            ):
                write_schematic.write()
            rendered = schematic.render(self.design)
            self.assertEqual(paths["SCHEMATIC"].read_text(), rendered)
            self.assertEqual(
                paths["SYMBOL_LIBRARY"].read_text(), render_symbol_library(rendered)
            )
            self.assertIn(
                '(uri "${KIPRJMOD}/generated-symbols.kicad_sym")',
                paths["SYMBOL_TABLE"].read_text(),
            )
            self.assertEqual(
                set(output.iterdir()),
                {paths["SCHEMATIC"], paths["SYMBOL_LIBRARY"], paths["SYMBOL_TABLE"]},
            )


if __name__ == "__main__":
    unittest.main()
