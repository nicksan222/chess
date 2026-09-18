"""Reusable Blender mesh, collection, boolean, and library helpers."""

from collections.abc import Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol, TypeVar, cast

import bpy
from mathutils import Vector

ObjectData = TypeVar("ObjectData")


class _LibrarySource(Protocol):
    objects: Sequence[str]


class _LibraryTarget(Protocol):
    objects: list[str | bpy.types.Object | None]


def active_object(operation: str) -> bpy.types.Object:
    """Return the operator result while narrowing Blender's optional context."""
    obj = bpy.context.object
    if obj is None:
        raise RuntimeError(f"Blender did not create an object during {operation}")
    return obj


def require_object(name: str) -> bpy.types.Object:
    """Look up a named object with a useful error instead of an untyped failure."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Scene is missing required object: {name}")
    return obj


# Blender 4.5 embeds Python 3.11, so this cannot use PEP 695 type parameters.
def require_object_data(  # noqa: UP047
    obj: bpy.types.Object, data_type: type[ObjectData]
) -> ObjectData:
    """Narrow Object.data to the kind required by the caller."""
    data = obj.data
    if not isinstance(data, data_type):
        raise TypeError(f"{obj.name} does not contain {data_type.__name__} data")
    return data


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
    obj = active_object(f"creating box {name}")
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
    _boolean_batch(body, cutters, name, "DIFFERENCE")


def union_batch(
    body: bpy.types.Object, additions: list[bpy.types.Object], name: str
) -> None:
    """Join additions into one operand and union them in a single pass.

    The same disjointness rule as `cut_batch` applies.
    """
    _boolean_batch(body, additions, name, "UNION")


def _boolean_batch(
    body: bpy.types.Object,
    operands: list[bpy.types.Object],
    name: str,
    operation: str,
) -> None:
    if not operands:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for operand in operands:
        operand.select_set(True)
    bpy.context.view_layer.objects.active = operands[0]
    if len(operands) > 1:
        bpy.ops.object.join()
    combined = active_object(f"joining boolean operand {name}")
    combined.name = name
    boolean_apply(body, combined, operation)
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
    obj = active_object(f"creating cylinder {name}")
    obj.name = name
    move_to_collection(obj, collection)
    return obj


def cylinder_between(
    name: str,
    diameter: float,
    position: tuple[float, float],
    bottom: float,
    top: float,
    collection: bpy.types.Collection,
    vertices: int = 64,
) -> bpy.types.Object:
    """A vertical cylinder defined by its physical bottom and top faces."""
    return cylinder(
        name,
        diameter,
        top - bottom,
        (*position, (bottom + top) / 2.0),
        collection,
        vertices,
    )


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
    obj.rotation_euler = (
        (target - obj.location)
        .to_track_quat("-Z", "Y")
        .to_euler("XYZ", obj.rotation_euler)
    )


def load_objects(
    blend_path: Path,
    object_names: tuple[str, ...],
) -> dict[str, bpy.types.Object]:
    """Load exact named source objects from a generated Blender library."""
    load_context = cast(
        AbstractContextManager[tuple[_LibrarySource, _LibraryTarget]],
        bpy.data.libraries.load(str(blend_path), link=False),
    )
    with load_context as (data_from, data_to):
        missing = set(object_names) - set(data_from.objects)
        if missing:
            raise RuntimeError(f"{blend_path} is missing objects: {sorted(missing)}")
        requested: list[str | bpy.types.Object | None] = list(object_names)
        data_to.objects = requested

    loaded: dict[str, bpy.types.Object] = {}
    for name, obj in zip(object_names, data_to.objects):
        if not isinstance(obj, bpy.types.Object):
            raise RuntimeError(f"{blend_path} returned no object for {name}")
        loaded[name] = obj
    return loaded
