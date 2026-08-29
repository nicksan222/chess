"""Reusable scene configuration and studio presentation helpers."""

import bpy
from mathutils import Vector

from core import modeling


TILE_STUDIO_LIGHTS = (
    ("Key_Light", (22.0, -28.0, 34.0), 82_000.0, 32.0, (1.0, 0.78, 0.58)),
    ("Fill_Light", (-32.0, 18.0, 24.0), 58_000.0, 28.0, (0.62, 0.78, 1.0)),
    ("Top_Rim_Light", (5.0, 12.0, 38.0), 68_000.0, 24.0, (1.0, 0.9, 0.72)),
    ("Underside_Fill", (15.0, -10.0, -28.0), 25_000.0, 22.0, (0.85, 0.9, 1.0)),
)
BOARD_STUDIO_LIGHTS = (
    ("Key_Light", (180.0, -220.0, 360.0), 1_150_000.0, 180.0, (1.0, 0.78, 0.58)),
    ("Fill_Light", (-260.0, 120.0, 220.0), 850_000.0, 160.0, (0.62, 0.78, 1.0)),
    ("Rim_Light", (40.0, 260.0, 300.0), 1_000_000.0, 150.0, (1.0, 0.9, 0.72)),
)


def configure_scene(
    name: str,
    scale_length: float,
    resolution: tuple[int, int],
    background_color: tuple[float, float, float, float],
    background_strength: float,
) -> bpy.types.Scene:
    scene = bpy.context.scene
    bpy.context.preferences.filepaths.save_version = 0
    scene.name = name
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.unit_settings.scale_length = scale_length
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = background_color
    background.inputs["Strength"].default_value = background_strength
    return scene


def add_studio(
    collection: bpy.types.Collection,
    floor_material: bpy.types.Material,
    floor_size: tuple[float, float],
    camera_location: tuple[float, float, float],
    camera_target: tuple[float, float, float],
    camera_lens: float,
    lights: tuple[
        tuple[
            str,
            tuple[float, float, float],
            float,
            float,
            tuple[float, float, float],
        ],
        ...,
    ],
) -> None:
    floor = modeling.rounded_box(
        "Studio_Floor",
        (*floor_size, 3.0),
        (0.0, 0.0, -1.5),
        2.0,
        collection,
    )
    floor.data.materials.append(floor_material)

    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object
    camera.name = "Camera_Render"
    camera.data.lens = camera_lens
    modeling.point_at(camera, Vector(camera_target))
    modeling.move_to_collection(camera, collection)
    bpy.context.scene.camera = camera

    for name, location, energy, size, color in lights:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        modeling.point_at(light, Vector(camera_target))
        modeling.move_to_collection(light, collection)
