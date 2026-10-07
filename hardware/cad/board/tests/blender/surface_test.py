"""Probe the actual seated mesh and both rendered views, not just dimensions."""

import sys
import tempfile
import unittest
from pathlib import Path
from typing import cast

from shared import dimensions


@unittest.skipUnless("bpy" in sys.modules, "Executed by the Blender generation worker")
class SurfaceTest(unittest.TestCase):
    def test_each_square_has_a_ring_channel_and_raised_center_island(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        inverse = plate.matrix_world.inverted()
        for square in dimensions.BOARD_SQUARES:
            with self.subTest(square=square.name):
                surface = dimensions.CASE_HEIGHT_MM - (
                    dimensions.TILE_PLATE_DARK_SQUARE_DEPTH_MM if square.is_dark else 0
                )
                # A square channel, not a solid square hole: the middle stays up.
                for dx, dy, depth in (
                    (0, 0, 0),
                    (6, 6, 0),
                    (8, 0, 0.8),
                    (-8, 0, 0.8),
                    (0, 8, 0.8),
                    (0, -8, 0.8),
                    (8, 8, 0.8),
                    (-8, 8, 0.8),
                    (8, -8, 0.8),
                    (-8, -8, 0.8),
                    (10, 0, 0),
                ):
                    origin = inverse @ Vector(
                        (
                            square.centre_mm[0] + dx,
                            square.centre_mm[1] + dy,
                            dimensions.CASE_HEIGHT_MM + 1,
                        )
                    )
                    hit, point, _, _ = plate.ray_cast(
                        cast(Vector, origin), Vector((0, 0, -1))
                    )
                    self.assertTrue(hit, "The ring channel must have a solid floor")
                    self.assertAlmostEqual(
                        (plate.matrix_world @ point).z, surface - depth, places=3
                    )
                underside = (
                    dimensions.CASE_HEIGHT_MM - dimensions.TILE_PLATE_THICKNESS_MM
                )
                for dx, dy in ((0, 0), (8, 8), (-8, -8)):
                    below = inverse @ Vector(
                        (
                            square.centre_mm[0] + dx,
                            square.centre_mm[1] + dy,
                            underside - 1,
                        )
                    )
                    hit, point, _, _ = plate.ray_cast(
                        cast(Vector, below), Vector((0, 0, 1))
                    )
                    self.assertTrue(hit)
                    self.assertAlmostEqual(
                        (plate.matrix_world @ point).z, underside, places=3
                    )

    def test_all_button_stems_protrude_through_the_plate(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        for button in dimensions.PANEL_BUTTONS:
            with self.subTest(button=button.switch_reference):
                stem = bpy.data.objects[f"PCB_{button.switch_reference}_Actuator"]
                top = max(
                    (stem.matrix_world @ Vector(corner)).z
                    for corner in cast(
                        tuple[tuple[float, float, float], ...], stem.bound_box
                    )
                )
                self.assertAlmostEqual(
                    top
                    - (dimensions.CASE_HEIGHT_MM - dimensions.PANEL_SURFACE_RECESS_MM),
                    2.0,
                    delta=0.01,  # KiCad mounting-face offset and GLB mesh precision.
                )
                origin = plate.matrix_world.inverted() @ Vector(
                    (*button.position_mm, top + 1)
                )
                hit, _, _, _ = plate.ray_cast(
                    cast(Vector, origin), Vector((0, 0, -1)), distance=5
                )
                self.assertFalse(hit, "Plate must not block the button stem")

    def test_finished_and_open_views_keep_the_electronics_visible(self) -> None:
        import bpy
        from mathutils import Vector

        from cad.harness.base.blender.render import render_views

        electronics = bpy.data.collections["ELECTRONICS_REFERENCE"]
        plate = bpy.data.objects["Printable_Tile_Plate"]
        seated = plate.location.copy()
        camera = bpy.data.objects["Camera_Render"]
        fill = bpy.data.objects["Fill_Light"]
        fill_data = fill.data
        finished_camera = (Vector((350, -450, 420)), 36.0)
        original_energy = fill_data.energy
        visibility: list[bool] = []
        energies: list[float] = []

        def capture(*args: object, **kwargs: object) -> None:
            visibility.append(not electronics.hide_render)
            energies.append(fill_data.energy)

        with tempfile.TemporaryDirectory() as directory:
            render_views(plate, electronics, Path(directory), render_still=capture)
        self.assertEqual(visibility, [True, True])
        self.assertEqual(energies[0], original_energy)
        self.assertGreater(energies[1], original_energy)
        self.assertEqual(plate.location, seated)
        self.assertEqual(camera.location, finished_camera[0])
        self.assertEqual(camera.data.lens, finished_camera[1])
        self.assertEqual(fill_data.energy, original_energy)
        self.assertEqual(
            bpy.context.scene.render.filepath, "//board-assembly-finished.png"
        )

    def test_render_failure_restores_the_finished_view(self) -> None:
        import bpy

        from cad.harness.base.blender.render import render_views

        electronics = bpy.data.collections["ELECTRONICS_REFERENCE"]
        plate = bpy.data.objects["Printable_Tile_Plate"]
        seated = plate.location.copy()
        camera = bpy.data.objects["Camera_Render"]
        fill = bpy.data.objects["Fill_Light"]
        original_energy = fill.data.energy
        calls = 0

        def fail_open_view() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("render failed")

        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(RuntimeError, "render failed"),
        ):
            render_views(
                plate, electronics, Path(directory), render_still=fail_open_view
            )
        self.assertEqual(calls, 2)
        self.assertEqual(plate.location, seated)
        self.assertFalse(electronics.hide_render)
        self.assertEqual(tuple(camera.location), (350, -450, 420))
        self.assertEqual(camera.data.lens, 36)
        self.assertEqual(fill.data.energy, original_energy)
        self.assertEqual(
            bpy.context.scene.render.filepath, "//board-assembly-finished.png"
        )

    def test_reopened_assembly_defaults_to_the_finished_view(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        electronics = bpy.data.collections["ELECTRONICS_REFERENCE"]
        camera = bpy.data.objects["Camera_Render"]
        fill = bpy.data.objects["Fill_Light"]
        floor = bpy.data.objects["Studio_Floor"]
        self.assertEqual(
            plate.location,
            Vector(
                (
                    0,
                    dimensions.TILE_PLATE_CENTER_Y_MM,
                    dimensions.CASE_HEIGHT_MM - dimensions.TILE_PLATE_THICKNESS_MM / 2,
                )
            ),
        )
        self.assertFalse(electronics.hide_render)
        self.assertEqual(camera.location, Vector((350, -450, 420)))
        self.assertEqual(camera.data.lens, 36)
        self.assertGreaterEqual(camera.data.clip_end, 5_000)
        self.assertEqual(fill.data.energy, 1_050_000)
        self.assertGreaterEqual(floor.dimensions.x, 5_000)
        self.assertGreaterEqual(floor.dimensions.y, 5_000)
        self.assertEqual(
            bpy.context.scene.render.filepath, "//board-assembly-finished.png"
        )

    def test_both_views_frame_the_complete_board_with_margin(self) -> None:
        import bpy
        from bpy_extras.object_utils import world_to_camera_view
        from mathutils import Vector

        from cad.harness.base.blender.render import render_views

        scene = bpy.context.scene
        plate = bpy.data.objects["Printable_Tile_Plate"]
        case = bpy.data.objects["Printable_Board_Case"]
        views: list[str] = []

        def capture() -> None:
            bpy.context.view_layer.update()
            camera = bpy.data.objects["Camera_Render"]
            views.append(Path(scene.render.filepath).name)
            for part in (case, plate):
                for corner in cast(
                    tuple[tuple[float, float, float], ...], part.bound_box
                ):
                    point = world_to_camera_view(
                        scene, camera, cast(Vector, part.matrix_world @ Vector(corner))
                    )
                    with self.subTest(view=views[-1], part=part.name, corner=corner):
                        self.assertGreater(point.z, 0)
                        for coordinate in (point.x, point.y):
                            self.assertGreaterEqual(coordinate, 0.03)
                            self.assertLessEqual(coordinate, 0.97)

        with tempfile.TemporaryDirectory() as directory:
            render_views(
                plate,
                bpy.data.collections["ELECTRONICS_REFERENCE"],
                Path(directory),
                render_still=capture,
            )
        self.assertEqual(
            views, ["board-assembly-finished.png", "board-assembly-open.png"]
        )

    def test_every_led_has_an_unobstructed_window(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        for square in dimensions.BOARD_SQUARES:
            with self.subTest(square=square.name):
                origin = plate.matrix_world.inverted() @ Vector(
                    (*square.led_position_mm, dimensions.CASE_HEIGHT_MM + 1)
                )
                hit, _, _, _ = plate.ray_cast(
                    cast(Vector, origin), Vector((0, 0, -1)), distance=5
                )
                self.assertFalse(hit, "LED window must pass through the entire plate")

    def test_display_is_visible_through_the_seated_plate(self) -> None:
        import bpy
        from mathutils import Vector

        origin = Vector(
            (
                *dimensions.PANEL_OLED_CENTER_MM,
                dimensions.CASE_HEIGHT_MM + dimensions.PANEL_OLED_MODULE_MM[2] + 2,
            )
        )
        hit, point, _, _, obj, _ = bpy.context.scene.ray_cast(
            bpy.context.evaluated_depsgraph_get(), origin, Vector((0, 0, -1))
        )
        self.assertTrue(hit)
        self.assertEqual(obj.name, "Proxy_Display_Module_Screen")
        self.assertAlmostEqual(
            point.z,
            dimensions.PANEL_OLED_SCREEN_Z_MM,
            places=3,
        )

    def test_control_strip_is_lower_than_the_playing_surface(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        origin = plate.matrix_world.inverted() @ Vector(
            (52, dimensions.PANEL_ORIGIN_Y_MM, dimensions.CASE_HEIGHT_MM + 1)
        )
        hit, point, _, _ = plate.ray_cast(cast(Vector, origin), Vector((0, 0, -1)))
        self.assertTrue(hit)
        self.assertAlmostEqual(
            (plate.matrix_world @ point).z, dimensions.CASE_HEIGHT_MM - 1.0, places=3
        )

    def test_every_square_has_its_chessboard_color(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        for square in dimensions.BOARD_SQUARES:
            with self.subTest(square=square.name):
                origin = plate.matrix_world.inverted() @ Vector(
                    (*square.centre_mm, dimensions.CASE_HEIGHT_MM + 1)
                )
                hit, _, _, index = plate.ray_cast(
                    cast(Vector, origin), Vector((0, 0, -1))
                )
                self.assertTrue(hit)
                material = plate.data.materials[
                    plate.data.polygons[index].material_index
                ]
                self.assertEqual(
                    material.name, "Dark squares" if square.is_dark else "Light squares"
                )

    def test_display_surround_is_part_of_the_lowered_strip(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        x, y = dimensions.PANEL_OLED_CENTER_MM
        origin = plate.matrix_world.inverted() @ Vector(
            (
                x,
                y + dimensions.PANEL_OLED_BEZEL_OUTER_MM[1] / 2 + 0.5,
                dimensions.CASE_HEIGHT_MM + 1,
            )
        )
        hit, point, _, _ = plate.ray_cast(cast(Vector, origin), Vector((0, 0, -1)))
        self.assertTrue(hit)
        self.assertAlmostEqual(
            (plate.matrix_world @ point).z, dimensions.CASE_HEIGHT_MM - 1.0, places=3
        )

    def test_display_carrier_does_not_overlap_the_screen_face(self) -> None:
        import bpy
        from mathutils import Vector

        carrier = bpy.data.objects["Proxy_Display_Module_Frame"]
        screen = bpy.data.objects["Proxy_Display_Module_Screen"]
        top = screen.location.z + screen.dimensions.z / 2
        for dx, dy in ((0, 0), (-8, -4), (-8, 4), (8, -4), (8, 4)):
            with self.subTest(offset=(dx, dy)):
                origin = carrier.matrix_world.inverted() @ Vector(
                    (screen.location.x + dx, screen.location.y + dy, top + 1)
                )
                hit, _, _, _ = carrier.ray_cast(
                    cast(Vector, origin), Vector((0, 0, -1)), distance=1.01
                )
                self.assertFalse(hit, "Carrier must not share the visible screen face")

    def test_display_mounts_have_carrier_support_and_blind_pilots(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        x, y = dimensions.PANEL_OLED_CENTER_MM
        for dx, dy in dimensions.PANEL_OLED_MOUNT_HOLES_MM:
            for offset, expected_z in (
                (0.0, dimensions.PCB_TOP_Z_MM + 1.5),
                (1.6, dimensions.PANEL_OLED_PCB_BOTTOM_Z_MM),
            ):
                with self.subTest(hole=(dx, dy), offset=offset):
                    origin = plate.matrix_world.inverted() @ Vector(
                        (
                            x + dx,
                            y + dy + offset,
                            dimensions.PANEL_OLED_PCB_BOTTOM_Z_MM + 0.1,
                        )
                    )
                    hit, point, _, _ = plate.ray_cast(
                        cast(Vector, origin), Vector((0, 0, -1))
                    )
                    self.assertTrue(
                        hit, "Display mounting pilot must retain a solid floor"
                    )
                    self.assertAlmostEqual(
                        (plate.matrix_world @ point).z, expected_z, places=3
                    )

    def test_each_display_screw_is_accessible_from_above(self) -> None:
        import bpy
        from mathutils import Vector

        plate = bpy.data.objects["Printable_Tile_Plate"]
        x, y = dimensions.PANEL_OLED_CENTER_MM
        # Probe the complete Ø4.5 screw head through the Ø5 service opening,
        # not just its centreline. It must reach the carrier without touching roof.
        for dx, dy in dimensions.PANEL_OLED_MOUNT_HOLES_MM:
            for sx, sy in ((0, 0), (2.25, 0), (-2.25, 0), (0, 2.25), (0, -2.25)):
                origin = plate.matrix_world.inverted() @ Vector(
                    (x + dx + sx, y + dy + sy, dimensions.PANEL_OLED_BEZEL_TOP_Z_MM + 1)
                )
                hit, _, _, _ = plate.ray_cast(
                    cast(Vector, origin),
                    Vector((0, 0, -1)),
                    distance=dimensions.PANEL_OLED_BEZEL_TOP_Z_MM
                    + 1
                    - dimensions.PANEL_OLED_PCB_BOTTOM_Z_MM
                    - dimensions.PANEL_OLED_PCB_THICKNESS_MM,
                )
                self.assertFalse(hit, "Bezel must admit the screw head and driver")

    def test_every_button_label_is_cut_into_the_panel(self) -> None:
        import bpy
        from mathutils import Vector

        from shared.panel_buttons import PANEL_BUTTONS

        plate = bpy.data.objects["Printable_Tile_Plate"]
        surface = dimensions.CASE_HEIGHT_MM - dimensions.PANEL_SURFACE_RECESS_MM
        font = bpy.data.fonts.load(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        )
        for button in PANEL_BUTTONS:
            x, y = button.legend_position_mm
            # A separately constructed reference word makes swapped or misspelled
            # labels fail, rather than accepting any recess near the button.
            bpy.ops.object.text_add(location=(x, y, surface))
            expected = cast(bpy.types.Object, bpy.context.object)
            text = cast(bpy.types.TextCurve, expected.data)
            text.body, text.align_x = button.name, "CENTER"
            text.font, text.size, text.extrude = (
                font,
                dimensions.PANEL_LEGEND_SIZE_MM,
                0.1,
            )
            bpy.ops.object.convert(target="MESH")
            bpy.context.view_layer.update()
            letters = 0
            half_word = int(expected.dimensions.x * 2) + 1
            for ix in range(-half_word, half_word + 1):
                for iy in range(1, 13):
                    world = Vector((x + ix / 4, y + iy / 4, surface + 1))
                    word_hit, _, _, _ = expected.ray_cast(
                        cast(Vector, expected.matrix_world.inverted() @ world),
                        Vector((0, 0, -1)),
                    )
                    hit, point, _, _ = plate.ray_cast(
                        cast(Vector, plate.matrix_world.inverted() @ world),
                        Vector((0, 0, -1)),
                    )
                    self.assertTrue(hit)
                    depth = surface - (plate.matrix_world @ point).z
                    with self.subTest(button=button.name, sample=(ix, iy)):
                        self.assertAlmostEqual(
                            depth,
                            dimensions.PANEL_LEGEND_DEPTH_MM if word_hit else 0.0,
                            delta=0.01,
                        )
                    letters += int(word_hit)
            self.assertGreater(letters, 5, "Reference word must have visible strokes")
            mesh = cast(bpy.types.Mesh, expected.data)
            bpy.data.objects.remove(expected, do_unlink=True)
            bpy.data.meshes.remove(mesh)

    def test_button_caps_are_separate_printable_parts_on_the_real_stems(self) -> None:
        import bpy
        from mathutils import Vector

        from cad.harness.base.blender.validation import overlap_volume_mm3
        from shared.panel_buttons import PANEL_BUTTONS

        plate = bpy.data.objects["Printable_Tile_Plate"]
        for button in PANEL_BUTTONS:
            cap = bpy.data.objects[f"Cap_{button.switch_reference}"]
            stem = bpy.data.objects[f"PCB_{button.switch_reference}_Actuator"]
            with self.subTest(button=button.name):
                self.assertAlmostEqual(cap.location.x, button.x_mm, places=3)
                self.assertAlmostEqual(cap.location.y, button.y_mm, places=3)
                self.assertEqual(cap["intended_process"], "Prototype FDM")
                self.assertLess(overlap_volume_mm3(cap, stem), 0.01)
                self.assertLess(overlap_volume_mm3(cap, plate), 0.01)
                origin = cap.matrix_world.inverted() @ Vector(
                    (*button.position_mm, dimensions.PANEL_BUTTON_CAP_BOTTOM_Z_MM - 0.1)
                )
                hit, point, _, _ = cap.ray_cast(cast(Vector, origin), Vector((0, 0, 1)))
                self.assertTrue(hit)
                socket_top = (cap.matrix_world @ point).z
                self.assertAlmostEqual(
                    socket_top, dimensions.PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM, places=3
                )
                stem_top = max(
                    (stem.matrix_world @ Vector(corner)).z
                    for corner in cast(
                        tuple[tuple[float, float, float], ...], stem.bound_box
                    )
                )
                self.assertGreater(
                    stem_top - dimensions.PANEL_BUTTON_CAP_BOTTOM_Z_MM, 1.0
                )
                self.assertLess(socket_top - stem_top, 0.2)
                self.assertGreater(
                    (
                        cap.matrix_world
                        @ Vector(
                            cast(tuple[tuple[float, float, float], ...], cap.bound_box)[
                                6
                            ]
                        )
                    ).z,
                    dimensions.CASE_HEIGHT_MM,
                )
