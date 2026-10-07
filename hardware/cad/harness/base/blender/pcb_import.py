"""Import a native KiCad GLB, keeping its mesh geometry and package transforms."""

from pathlib import Path
from typing import cast

import bpy
from mathutils import Matrix, Vector

from cad.harness.base.pcb import PcbSnapshot
from shared import dimensions

from . import modeling, validation


def import_board(
    source: Path,
    snapshot: PcbSnapshot,
    reference: str,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    before = set(bpy.data.objects)
    # Blender's importer otherwise applies the scene's millimetre scale itself.
    # Read GLB metres consistently, then apply our single assembly transform.
    units = bpy.context.scene.unit_settings
    previous_scale = units.scale_length
    try:
        units.scale_length = 1.0
        bpy.ops.import_scene.gltf(filepath=str(source))
    finally:
        units.scale_length = previous_scale
    imported = tuple(obj for obj in bpy.data.objects if obj not in before)
    if not imported:
        raise RuntimeError("KiCad import produced no objects")
    by_name = {obj.name: obj for obj in imported}
    package_roots = {
        part.reference: by_name.get(part.reference) for part in snapshot.parts
    }
    if any(obj is None for obj in package_roots.values()):
        raise RuntimeError("KiCad import is missing PCB component references")
    package_meshes: dict[bpy.types.Object, tuple[str, str]] = {}
    for pcb_reference, node in package_roots.items():
        assert node is not None
        meshes = tuple(
            child
            for child in cast(tuple[bpy.types.Object, ...], node.children_recursive)
            if child.type == "MESH"
        )
        if not meshes:
            raise RuntimeError(f"{pcb_reference}: imported model has no mesh")
        for mesh in meshes:
            package_meshes[mesh] = (pcb_reference, mesh.name.split(".")[0])
    # glTF metres -> our millimetre scene; KiCad's XY origin is the PCB center.
    transform = Matrix.Translation(
        Vector((0, dimensions.PCB_CENTER_OFFSET_Y_MM, dimensions.PCB_UNDERSIDE_Z_MM))
    ) @ Matrix(((1000, 0, 0, 0), (0, 1000, 0, 0), (0, 0, 1000, 0), (0, 0, 0, 1)))
    matrices = {obj: obj.matrix_world.copy() for obj in imported}
    root = bpy.data.objects.new(reference, None)  # pyright: ignore[reportArgumentType]
    collection.objects.link(root)
    substrate = 0
    for index, obj in enumerate(imported):
        obj.parent = None
        obj.matrix_world = transform @ matrices[obj]
        obj.parent = root
        if obj in package_meshes:
            pcb_reference, solid_name = package_meshes[obj]
            obj.name = f"PCB_{pcb_reference}_{solid_name}"
            obj["pcb_reference"] = pcb_reference
            obj["fit_check"] = True
        elif obj.type == "EMPTY" and obj.name in package_roots:
            obj.name = f"PCB_{obj.name}"
        elif obj.type == "MESH":
            mesh = modeling.require_object_data(obj, bpy.types.Mesh)
            if mesh.name.endswith("_PCB"):
                obj.name = "PCB_Substrate"
                obj["fit_check"] = True
                substrate += 1
            else:
                obj.name = f"PCB_Artwork_{index}"
                obj["fit_check"] = False
        else:
            obj.name = f"PCB_Node_{index}"
        obj["source"] = source.name
        modeling.move_to_collection(obj, collection)
        if obj.type == "MESH":
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            if obj.get("fit_check", False):
                validation.weld_solid(obj)
    if substrate != 1:
        raise RuntimeError("KiCad import must contain exactly one PCB substrate")
    root["source"] = source.name
    root["component_count"] = len(snapshot.parts)
    root["geometry_rebuilt"] = False
    bpy.context.view_layer.update()
    return root
