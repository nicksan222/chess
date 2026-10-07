"""Inspect the real imported KiCad assembly and its off-board components."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, cast

from cad.harness.base.pcb import PcbSnapshot
from shared import dimensions

if TYPE_CHECKING:
    import bpy


@unittest.skipUnless("bpy" in sys.modules, "Executed by the Blender generation worker")
class ElectronicsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import bpy

        cls.snapshot = PcbSnapshot.read(
            Path(bpy.data.filepath).parent / "pcb-components.json"
        )

    def bounds(self, obj: bpy.types.Object) -> tuple[tuple[float, float], ...]:
        from mathutils import Vector

        points = [
            cast(Vector, obj.matrix_world @ Vector(corner))
            for corner in cast(tuple[tuple[float, float, float], ...], obj.bound_box)
        ]
        return tuple(
            (min(p[axis] for p in points), max(p[axis] for p in points))
            for axis in range(3)
        )

    def test_every_component_is_imported_at_its_pcb_position_and_side(self) -> None:
        import bpy

        for part in self.snapshot.parts:
            with self.subTest(reference=part.reference):
                node = bpy.data.objects[f"PCB_{part.reference}"]
                self.assertEqual(node["source"], "chess-board.glb")
                self.assertAlmostEqual(
                    node.matrix_world.translation.x, part.position_mm[0], places=3
                )
                self.assertAlmostEqual(
                    node.matrix_world.translation.y, part.position_mm[1], places=3
                )
                body = bpy.data.objects[f"PCB_{part.reference}_Body"]
                bounds = self.bounds(body)
                if part.bottom:
                    self.assertLess(bounds[2][1], dimensions.PCB_UNDERSIDE_Z_MM)
                else:
                    self.assertGreater(bounds[2][0], dimensions.PCB_UNDERSIDE_Z_MM)
                local = cast(tuple[tuple[float, float, float], ...], body.bound_box)
                expected = part.housing_mm or part.body_mm
                for axis in range(3):
                    self.assertAlmostEqual(
                        max(p[axis] for p in local) - min(p[axis] for p in local),
                        expected[axis],
                        places=3,
                    )
                angle = math.radians(part.rotation_degrees)
                width = (
                    abs(math.cos(angle)) * expected[0]
                    + abs(math.sin(angle)) * expected[1]
                )
                height = (
                    abs(math.sin(angle)) * expected[0]
                    + abs(math.cos(angle)) * expected[1]
                )
                self.assertAlmostEqual(bounds[0][1] - bounds[0][0], width, places=3)
                self.assertAlmostEqual(bounds[1][1] - bounds[1][0], height, places=3)
                self.assertAlmostEqual(
                    sum(bounds[0]) / 2, part.position_mm[0], places=3
                )
                self.assertAlmostEqual(
                    sum(bounds[1]) / 2, part.position_mm[1], places=3
                )

    def test_buttons_have_their_real_imported_housing_and_actuator(self) -> None:
        import bpy

        for reference in self.snapshot.buttons.values():
            part = next(
                part for part in self.snapshot.parts if part.reference == reference
            )
            body, stem = (
                bpy.data.objects[f"PCB_{reference}_{solid}"]
                for solid in ("Body", "Actuator")
            )
            body_bounds, stem_bounds = self.bounds(body), self.bounds(stem)
            body_z, stem_z = body_bounds[2], stem_bounds[2]
            with self.subTest(reference=reference):
                self.assertAlmostEqual(
                    sum(stem_bounds[0]) / 2, part.position_mm[0], places=3
                )
                self.assertAlmostEqual(
                    sum(stem_bounds[1]) / 2, part.position_mm[1], places=3
                )
                self.assertAlmostEqual(
                    stem_bounds[0][1] - stem_bounds[0][0],
                    dimensions.PANEL_BUTTON_ACTUATOR_DIAMETER_MM,
                    places=3,
                )
                self.assertAlmostEqual(
                    stem_bounds[1][1] - stem_bounds[1][0],
                    dimensions.PANEL_BUTTON_ACTUATOR_DIAMETER_MM,
                    places=3,
                )
                self.assertAlmostEqual(
                    stem_bounds[2][1] - stem_bounds[2][0],
                    dimensions.PANEL_BUTTON_HEIGHT_MM
                    - dimensions.PANEL_BUTTON_BODY_MM[2],
                    places=3,
                )
            self.assertAlmostEqual(stem_z[0], body_z[1], places=3)
            self.assertAlmostEqual(
                stem_z[1] - body_z[0], dimensions.PANEL_BUTTON_HEIGHT_MM, places=3
            )

    def test_substrate_has_the_exported_outline_and_mounting_holes(self) -> None:
        import bpy
        from mathutils import Vector

        board = bpy.data.objects["PCB_Substrate"]
        bounds = self.bounds(board)
        self.assertAlmostEqual(
            bounds[0][1] - bounds[0][0], dimensions.PCB_SIZE_MM[0], places=3
        )
        self.assertAlmostEqual(
            bounds[1][1] - bounds[1][0], dimensions.PCB_SIZE_MM[1], places=3
        )
        self.assertAlmostEqual(bounds[2][0], dimensions.PCB_UNDERSIDE_Z_MM, places=3)
        for x, y in dimensions.PCB_SUPPORT_POSITIONS_MM:
            origin = board.matrix_world.inverted() @ Vector(
                (x, y, dimensions.PCB_TOP_Z_MM + 1)
            )
            hit, _, _, _ = board.ray_cast(
                cast(Vector, origin), Vector((0, 0, -1)), distance=5
            )
            self.assertFalse(
                hit, "Imported mounting hole must pass through the substrate"
            )

    def test_import_contains_native_copper_and_artwork(self) -> None:
        import bpy

        artwork = [
            obj
            for obj in bpy.data.objects
            if obj.name.startswith("PCB_Artwork_") and obj.type == "MESH"
        ]
        self.assertGreater(len(artwork), 0)
        self.assertTrue(
            all(cast(str, obj["source"]) == "chess-board.glb" for obj in artwork)
        )
        self.assertFalse(bpy.data.objects["PCB_Assembly"]["geometry_rebuilt"])

    def test_off_board_host_and_display_keep_the_shared_placements(self) -> None:
        import bpy

        host = bpy.data.objects["Proxy_Host_Board"]
        self.assertAlmostEqual(host.location.x, dimensions.PI_CENTER_MM[0], places=3)
        self.assertAlmostEqual(host.location.y, dimensions.PI_CENTER_MM[1], places=3)
        host_bounds = self.bounds(host)
        x, y, z = dimensions.PI_BOARD_SIZE_MM
        turned = int(dimensions.PI_ROTATION_DEG) % 180 == 90
        for axis, size in enumerate((y, x, z) if turned else (x, y, z)):
            self.assertAlmostEqual(
                host_bounds[axis][1] - host_bounds[axis][0], size, places=3
            )
        self.assertAlmostEqual(host_bounds[2][1], dimensions.PI_TOP_FACE_Z_MM, places=3)
        display = bpy.data.objects["Proxy_Display_Module"]
        self.assertAlmostEqual(
            display.location.x, dimensions.PANEL_OLED_CENTER_MM[0], places=3
        )
        self.assertAlmostEqual(
            display.location.y, dimensions.PANEL_OLED_CENTER_MM[1], places=3
        )

        display_bounds = self.bounds(display)
        for axis, size in enumerate(
            (
                *dimensions.PANEL_OLED_MODULE_MM[:2],
                dimensions.PANEL_OLED_PCB_THICKNESS_MM,
            )
        ):
            self.assertAlmostEqual(
                display_bounds[axis][1] - display_bounds[axis][0], size, places=3
            )
        self.assertAlmostEqual(
            display_bounds[2][0], dimensions.PANEL_OLED_PCB_BOTTOM_Z_MM, places=3
        )
        underside = bpy.data.objects["Proxy_Display_Module_Underside"]
        self.assertGreater(self.bounds(underside)[2][0], dimensions.PCB_TOP_Z_MM + 0.5)
