"""Native KiCad objects remain authoritative for instantiated board geometry."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
for path in (PCB_ROOT, HARDWARE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from base.kicad.api import pcbnew
except ModuleNotFoundError:  # Host-only unit runs do not install KiCad.
    pcbnew = None

if pcbnew is not None:
    from base import rules, sources
    from base.kicad import board as kicad
    from board import definition
    from board.wiring import geometry as board_builder
    from components.hall_sensor import HallSensorPin


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class KiCadBoardAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = sources.netlist()
        cls.design = definition.from_contract(cls.contract)
        cls.placements = cls.design.placements

    def layout_for(self, references: set[str]):
        layout = kicad.KiCadBoard(self.design)
        for reference in references:
            layout.attach(self.design.component(reference))
        return layout

    def test_native_board_owns_reviewed_manufacturing_rules(self) -> None:
        layout = kicad.KiCadBoard(self.design)
        settings = layout.native.GetDesignSettings()
        self.assertEqual(layout.native.GetCopperLayerCount(), rules.COPPER_LAYERS)
        self.assertAlmostEqual(
            pcbnew.ToMM(settings.m_MinClearance),
            rules.CLEARANCE_MM,
        )
        self.assertAlmostEqual(
            pcbnew.ToMM(settings.m_TrackMinWidth),
            rules.TRACE_WIDTH_MM,
        )

    def test_native_outline_matches_shared_board_dimensions(self) -> None:
        layout = kicad.KiCadBoard(self.design)
        board_builder.BoardGeometry(layout).add_mechanical_features()
        bounds = layout.native.GetBoardEdgesBoundingBox()
        width, height, _thickness = sources.dimensions().PCB_SIZE_MM
        # KiCad's native edge bounding box includes the Edge.Cuts stroke.
        self.assertAlmostEqual(
            pcbnew.ToMM(bounds.GetWidth()),
            width + board_builder.BOARD_EDGE_WIDTH_MM,
        )
        self.assertAlmostEqual(
            pcbnew.ToMM(bounds.GetHeight()),
            height + board_builder.BOARD_EDGE_WIDTH_MM,
        )

    def test_native_mounting_holes_match_shared_supports(self) -> None:
        layout = kicad.KiCadBoard(self.design)
        board_builder.BoardGeometry(layout).add_mechanical_features()
        holes = [
            footprint
            for footprint in layout.native.GetFootprints()
            if footprint.GetReference().startswith("H")
        ]
        shared = sources.dimensions()
        self.assertEqual(len(holes), len(shared.PCB_SUPPORT_POSITIONS_MM))
        for footprint in holes:
            pad = next(iter(footprint.Pads()))
            self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_NPTH)
            self.assertAlmostEqual(
                pcbnew.ToMM(pad.GetDrillSize().x),
                shared.PCB_MOUNTING_HOLE_DIAMETER_MM,
            )

    def test_front_silkscreen_labels_square_and_service_connections(self) -> None:
        layout = kicad.KiCadBoard(self.design)
        board_builder.BoardGeometry(layout).add_mechanical_features()
        labels = {
            drawing.GetText()
            for drawing in layout.native.GetDrawings()
            if isinstance(drawing, pcbnew.PCB_TEXT)
        }
        self.assertTrue(
            {f"{file}{rank}" for file in "ABCDEFGH" for rank in range(1, 9)} <= labels
        )
        self.assertTrue(set(board_builder.PI_HEADER_PINOUT) <= labels)
        self.assertIn("U1  I2C 0x20  A1-D4", labels)
        self.assertIn("U5  SPI 3V3 -> LED 5V", labels)
        self.assertIn("LED DATA + CLK IN", labels)
        self.assertIn("LED CHAIN END", labels)

    def test_attached_hall_pads_use_native_kicad_nets(self) -> None:
        layout = self.layout_for({"HS1"})
        output = layout.pad(("HS1", HallSensorPin.ACTIVE_LOW_OUTPUT))
        self.assertEqual(output.GetNetname(), "SQ_A1")
        native_hall = layout.native.FindFootprintByReference("HS1")
        self.assertEqual(native_hall.FindPadByNumber("2").GetNetname(), "SQ_A1")
        self.assertEqual(len(layout.native.GetFootprints()), 1)

    def test_every_component_materializes_with_native_kicad_nets(self) -> None:
        references = {item.reference for item in self.placements}
        layout = self.layout_for(references)
        self.assertEqual(len(layout.native.GetFootprints()), len(references))
        self.assertEqual(
            set(layout.pads),
            {
                (item.reference, logical)
                for item in self.placements
                for logical, _physical, _position, _definition in item.pads()
            },
        )
        for footprint in layout.native.GetFootprints():
            for pad in footprint.Pads():
                with self.subTest(
                    reference=footprint.GetReference(),
                    pad=pad.GetNumber(),
                ):
                    self.assertNotEqual(pad.GetNetCode(), 0)

    def test_one_square_materializes_as_four_native_footprints(self) -> None:
        references = {
            reference
            for reference, entry in self.contract["components"].items()
            if entry["extras"].get("Square") == "A1"
        }
        layout = self.layout_for(references)
        native_references = {
            footprint.GetReference() for footprint in layout.native.GetFootprints()
        }
        self.assertEqual(native_references, references)
        self.assertEqual(len(layout.pads), 13)

    def test_even_rank_led_keeps_its_native_rotation(self) -> None:
        led = next(
            item
            for item in self.placements
            if self.contract["components"][item.reference]["extras"].get("Square")
            == "A2"
            and self.contract["components"][item.reference]["part_key"] == "SK9822"
        )
        layout = self.layout_for({led.reference})
        native = layout.native.FindFootprintByReference(led.reference)
        self.assertAlmostEqual(native.GetOrientationDegrees(), 180.0)


if __name__ == "__main__":
    unittest.main()
