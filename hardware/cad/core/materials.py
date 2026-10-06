"""Shared procedural materials for Chess CAD presentation renders.

These make review renders readable only; they do not specify a purchased material,
finish or process for the printed parts.
"""

import bpy


def solid(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    """A plain Principled-BSDF material: `color` is RGBA, values 0-1.

    `color` is also set as the viewport colour so solid-mode previews match the render.
    """
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material
