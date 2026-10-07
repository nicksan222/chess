"""Inspect off-board parts and every proposed conductor in the seated model."""

from __future__ import annotations

import sys
import unittest
from collections.abc import Iterable
from typing import cast

from shared.electronics.harness import HARNESSES


@unittest.skipUnless("bpy" in sys.modules, "Executed by the Blender generation worker")
class HarnessTest(unittest.TestCase):
    def test_aabb_broadphase_keeps_only_possible_collision_pairs(self) -> None:
        import bpy

        from cad.harness.base.blender import modeling, validation
        from cad.harness.base.blender.render import (
            FIT_NOISE_TOLERANCE_MM3,
            fit_pair_exempt,
        )

        collection = bpy.context.scene.collection
        first = modeling.rounded_box(
            "BroadphaseFirst", (2, 2, 2), (0, 0, 0), 0, collection
        )
        touching = modeling.rounded_box(
            "BroadphaseTouching", (2, 2, 2), (2, 0, 0), 0, collection
        )
        overlapping = modeling.rounded_box(
            "BroadphaseOverlapping", (2, 2, 2), (1.99, 0, 0), 0, collection
        )
        distant = modeling.rounded_box(
            "BroadphaseDistant", (2, 2, 2), (10, 0, 0), 0, collection
        )
        objects = (first, touching, overlapping, distant)
        try:
            pairs = tuple(validation.aabb_overlap_pairs(objects))
            self.assertEqual(pairs, ((first, overlapping), (overlapping, touching)))
            first["source"] = overlapping["source"] = "chess-board.glb"
            first["physical_reference"] = "SW1"
            overlapping["physical_reference"] = "SW2"
            self.assertFalse(fit_pair_exempt(first, overlapping))
            self.assertLess(validation.overlap_volume_mm3(first, overlapping), 1.0)
            self.assertGreater(
                validation.overlap_volume_mm3(first, overlapping),
                FIT_NOISE_TOLERANCE_MM3,
            )
            overlapping["physical_reference"] = "SW1"
            self.assertTrue(fit_pair_exempt(first, overlapping))
        finally:
            for obj in objects:
                mesh = modeling.require_object_data(obj, bpy.types.Mesh)
                bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.meshes.remove(mesh)

    def test_panel_parts_and_mating_housings_are_in_the_assembly(self) -> None:
        import bpy

        for name in (
            "BARREL_JACK_Body",
            "BARREL_JACK_Bushing",
            "BARREL_JACK_Washer",
            "BARREL_JACK_Nut",
            "POWER_SWITCH_Body",
            "POWER_SWITCH_Face",
            "ROCKER_RECEPTACLE_1",
            "ROCKER_RECEPTACLE_2",
            "Mate_J2_housing",
            "Mate_J2_wire_exit",
            "Mate_J4_housing",
            "Mate_J4_wire_exit",
        ):
            obj = bpy.data.objects[name]
            self.assertEqual(obj.type, "MESH")
            self.assertTrue(all(axis > 0 for axis in obj.dimensions))

    def test_wire_exit_reservation_only_exempts_its_own_connector_wires(self) -> None:
        import bpy

        from cad.harness.base.blender.render import fit_pair_exempt

        wire_exit = bpy.data.objects["Mate_J2_wire_exit"]
        housing = bpy.data.objects["Mate_J2_housing"]
        own_wire = bpy.data.objects["Wire_J2_1"]
        other_wire = bpy.data.objects["Wire_J4_1"]
        self.assertTrue(fit_pair_exempt(wire_exit, own_wire))
        self.assertFalse(fit_pair_exempt(wire_exit, other_wire))
        self.assertFalse(fit_pair_exempt(housing, own_wire))

    def test_every_conductor_retains_its_cavity_net_and_cut_length(self) -> None:
        import bmesh
        import bpy

        from cad.harness.base.blender import modeling

        wires = tuple(w for group in HARNESSES.values() for w in group)
        for wire in wires:
            obj = bpy.data.objects[f"Wire_{wire.connector}_{wire.cavity}"]
            with self.subTest(name=obj.name):
                self.assertEqual(obj["connector"], wire.connector)
                self.assertEqual(obj["cavity"], str(wire.cavity))
                self.assertEqual(obj["net"], wire.net)
                self.assertEqual(obj["cut_length_mm"], wire.length_mm)
                self.assertLessEqual(
                    cast(float, obj["route_length_mm"]), wire.length_mm
                )
                self.assertGreater(cast(float, obj["route_length_mm"]), 0)
                bm = bmesh.new()
                bm.from_mesh(modeling.require_object_data(obj, bpy.types.Mesh))
                try:
                    self.assertTrue(
                        all(
                            edge.is_manifold
                            for edge in cast(Iterable[bmesh.types.BMEdge], bm.edges)
                        )
                    )
                    self.assertGreater(bm.calc_volume(signed=True), 0)
                finally:
                    bm.free()

    def test_endpoint_contact_does_not_hide_a_collision_mid_wire(self) -> None:
        import bpy

        from cad.harness.base.blender import modeling, validation

        collection = bpy.context.scene.collection
        wire = modeling.rounded_box(
            "RegressionWire", (20, 1, 1), (0, 0, 0), 0, collection
        )
        mate = modeling.rounded_box(
            "RegressionMate", (2, 2, 2), (0, 0, 0), 0, collection
        )
        try:
            self.assertGreater(
                validation.overlap_volume_mm3(
                    wire, mate, ((-10, 0, 0), (10, 0, 0)), 1.5
                ),
                1,
            )
            self.assertLess(
                validation.overlap_volume_mm3(wire, mate, ((0, 0, 0),), 3), 0.01
            )
        finally:
            for obj in (wire, mate):
                mesh = modeling.require_object_data(obj, bpy.types.Mesh)
                bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.meshes.remove(mesh)
