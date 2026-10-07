"""Reusable scene configuration and studio presentation helpers.

Role: render settings and a simple studio (floor, camera, area lights) shared by every
CAD project so all review renders look alike. Presentation only: nothing here affects
printable geometry.
"""

import bpy
from mathutils import Vector

from cad.harness.base.blender import modeling

# Three-point lighting for board renders. Each entry: name, location (mm), energy,
# disk size, RGB colour. Broad, near-neutral lights reveal recesses and dark parts.
BOARD_STUDIO_LIGHTS = (
    ("Key_Light", (180.0, -220.0, 420.0), 1_250_000.0, 260.0, (1.0, 0.94, 0.88)),
    ("Fill_Light", (-260.0, -150.0, 260.0), 1_050_000.0, 240.0, (0.86, 0.92, 1.0)),
    ("Rim_Light", (40.0, 260.0, 320.0), 950_000.0, 220.0, (1.0, 0.97, 0.92)),
)


def configure_scene(
    name: str,
    scale_length: float,
    resolution: tuple[int, int],
    background_color: tuple[float, float, float, float],
    background_strength: float,
) -> bpy.types.Scene:
    """Set units, EEVEE render settings and the world background on the current scene.

    Millimetre units with `scale_length` so Blender distances match the shared
    dimensions. Output is opaque 8-bit RGBA PNG.
    """
    scene = bpy.context.scene
    # Do not leave a `.blend1` backup beside every saved model.
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
    """Add a rounded floor, a camera aimed at `camera_target` and the given lights.

    Everything goes into `collection` (the PRESENTATION collection) so it can be told
    apart from the printable part. Each light entry follows `BOARD_STUDIO_LIGHTS`.
    """
    floor = modeling.rounded_box(
        "Studio_Floor",
        (*floor_size, 3.0),
        (0.0, 0.0, -1.5),
        1.0,
        collection,
    )
    floor.data.materials.append(floor_material)

    bpy.ops.object.camera_add(location=camera_location)
    camera = modeling.active_object("creating the render camera")
    camera.name = "Camera_Render"
    camera_data = modeling.require_object_data(camera, bpy.types.Camera)
    camera_data.lens = camera_lens
    camera_data.clip_end = max(floor_size)
    modeling.point_at(camera, Vector(camera_target))
    modeling.move_to_collection(camera, collection)
    bpy.context.scene.camera = camera

    for name, location, energy, size, color in lights:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = modeling.active_object(f"creating studio light {name}")
        light.name = name
        light_data = modeling.require_object_data(light, bpy.types.AreaLight)
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light_data.color = color
        modeling.point_at(light, Vector(camera_target))
        modeling.move_to_collection(light, collection)
