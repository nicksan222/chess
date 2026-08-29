"""Reusable Blender mesh, collection, boolean, and library helpers."""

from math import cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def new_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(
    obj: bpy.types.Object, collection: bpy.types.Collection
) -> None:
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)


def rounded_box(
    name: str,
    dimensions: tuple[float, float, float],
    location: tuple[float, float, float],
    radius: float,
    collection: bpy.types.Collection,
    bevel_segments: int = 4,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if radius > 0.0:
        bevel = obj.modifiers.new(name="Rounded edges", type="BEVEL")
        bevel.width = radius
        bevel.segments = bevel_segments
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    move_to_collection(obj, collection)
    return obj


def cylinder(
    name: str,
    diameter: float,
    height: float,
    location: tuple[float, float, float],
    collection: bpy.types.Collection,
    vertices: int = 64,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=height,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    return obj


def annular_cutter(
    name: str,
    outer_diameter: float,
    inner_diameter: float,
    bottom: float,
    top: float,
    collection: bpy.types.Collection,
    segments: int = 96,
) -> bpy.types.Object:
    outer_radius = outer_diameter / 2.0
    inner_radius = inner_diameter / 2.0
    vertices = []
    for radius, z in (
        (outer_radius, bottom),
        (outer_radius, top),
        (inner_radius, bottom),
        (inner_radius, top),
    ):
        for index in range(segments):
            angle = 2.0 * pi * index / segments
            vertices.append((radius * cos(angle), radius * sin(angle), z))

    faces = []
    for index in range(segments):
        next_index = (index + 1) % segments
        faces.extend(
            (
                (index, next_index, segments + next_index, segments + index),
                (
                    2 * segments + index,
                    3 * segments + index,
                    3 * segments + next_index,
                    2 * segments + next_index,
                ),
                (
                    segments + index,
                    segments + next_index,
                    3 * segments + next_index,
                    3 * segments + index,
                ),
                (
                    index,
                    2 * segments + index,
                    2 * segments + next_index,
                    next_index,
                ),
            )
        )

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cutter = bpy.data.objects.new(name, mesh)
    collection.objects.link(cutter)
    return cutter


def boolean_apply(
    body: bpy.types.Object, operand: bpy.types.Object, operation: str
) -> None:
    modifier = body.modifiers.new(
        name=f"{operation.title()} {operand.name}", type="BOOLEAN"
    )
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = operand
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    body.select_set(False)


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def load_objects(
    blend_path: Path,
    object_names: tuple[str, ...],
) -> dict[str, bpy.types.Object]:
    """Load exact named source objects from a generated Blender library."""
    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
        missing = set(object_names) - set(data_from.objects)
        if missing:
            raise RuntimeError(f"{blend_path} is missing objects: {sorted(missing)}")
        data_to.objects = list(object_names)
    return dict(zip(object_names, data_to.objects))
