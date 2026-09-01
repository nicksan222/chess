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


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
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
    # A bevel wider than half the thinnest dimension folds through itself. The
    # result is not an error in Blender, it is a silently invalid mesh that only
    # surfaces later as a failed manifold check, so refuse it here instead.
    if radius > 0.0 and radius >= min(dimensions) / 2.0:
        raise ValueError(
            f"{name}: bevel radius {radius} mm needs a dimension over "
            f"{2.0 * radius} mm, but the box is {min(dimensions)} mm at its thinnest"
        )
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


def box_between(
    name: str,
    bounds: tuple[float, float, float, float, float, float],
    collection: bpy.types.Collection,
    radius: float = 0.0,
) -> bpy.types.Object:
    """A box defined by its own extents rather than a centre and a size.

    A cutter that breaks a surface has to overhang it. Sizing from explicit
    bounds is what keeps a cutter face from landing exactly on the face it
    crosses, where a coplanar pair defeats the exact boolean solver.
    """
    x0, x1, y0, y1, z0, z1 = bounds
    return rounded_box(
        name,
        (x1 - x0, y1 - y0, z1 - z0),
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
        radius,
        collection,
    )


def cut_batch(
    body: bpy.types.Object, cutters: list[bpy.types.Object], name: str
) -> None:
    """Join cutters into one operand and subtract them in a single pass.

    Parts here carry hundreds of features, and one solver call each would
    dominate the build.

    Every cutter in a batch must be disjoint from the others. Joining is a mesh
    concatenation, not a union, so overlapping members produce a
    self-intersecting operand and the exact solver deletes the body outright
    rather than reporting a problem. Features that overlap each other, such as
    crossing grooves or a screw shaft and its head recess, belong in separate
    batches.
    """
    if not cutters:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for cutter in cutters:
        cutter.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]
    if len(cutters) > 1:
        bpy.ops.object.join()
    combined = bpy.context.object
    combined.name = name
    boolean_apply(body, combined, "DIFFERENCE")
    bpy.data.objects.remove(combined, do_unlink=True)


def union_batch(
    body: bpy.types.Object, additions: list[bpy.types.Object], name: str
) -> None:
    """Join additions into one operand and union them in a single pass.

    The same disjointness rule as `cut_batch` applies.
    """
    if not additions:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for addition in additions:
        addition.select_set(True)
    bpy.context.view_layer.objects.active = additions[0]
    if len(additions) > 1:
        bpy.ops.object.join()
    combined = bpy.context.object
    combined.name = name
    boolean_apply(body, combined, "UNION")
    bpy.data.objects.remove(combined, do_unlink=True)


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
